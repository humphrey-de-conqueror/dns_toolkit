
import argparse
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


CONFIG_PATH = Path("/etc/bind/named.conf")
INCLUDE_PATH = Path("/etc/bind/dns-toolkit-zones.conf")
ZONE_DIRECTORY = Path("/etc/bind/zones")
BACKUP_ROOT = Path("/var/lib/dns-toolkit/backups")
SERVICE_NAME = "bind9"


def run_command(
        command: list[str],
        timeout: float = 30.0,
) -> tuple[bool, str]:
        try:
                result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=timeout,
                )
        except (OSError, subprocess.TimeoutExpired) as error:
                return False, str(error)

        output = "\n".join(
                part
                for part in (result.stdout, result.stderr)
                if part
        )

        return result.returncode == 0, output


def validate_destination(destination: Path) -> None:
        if destination in {CONFIG_PATH, INCLUDE_PATH}:
                return

        if (
                destination.parent == ZONE_DIRECTORY
                and destination.name.startswith("db.")
                and destination.name not in {"db.", "db.."}
        ):
                return

        raise ValueError(
                f"Destination is not permitted: {destination}"
        )


def load_manifest(path: Path) -> dict[Path, str]:
        if not path.is_absolute():
                raise ValueError("Manifest path must be absolute.")

        if path.is_symlink() or not path.is_file():
                raise ValueError("Manifest must be a regular file.")

        payload = json.loads(path.read_text(encoding="utf-8"))

        if payload.get("version") != 1:
                raise ValueError("Unsupported manifest version.")

        if Path(payload.get("config_path", "")) != CONFIG_PATH:
                raise ValueError("Unexpected BIND configuration path.")

        if payload.get("service_name") != SERVICE_NAME:
                raise ValueError("Unexpected BIND service name.")

        entries = payload.get("files")

        if not isinstance(entries, list) or not entries:
                raise ValueError("Manifest contains no files.")

        files: dict[Path, str] = {}

        for entry in entries:
                if not isinstance(entry, dict):
                        raise ValueError("Invalid manifest entry.")

                destination = Path(entry.get("destination", ""))
                content = entry.get("content")

                validate_destination(destination)

                if not isinstance(content, str):
                        raise ValueError("File content must be text.")

                if destination in files:
                        raise ValueError(
                                f"Duplicate destination: {destination}"
                        )

                files[destination] = content

        if CONFIG_PATH not in files or INCLUDE_PATH not in files:
                raise ValueError(
                        "Manifest must contain named.conf and the "
                        "managed zone include."
                )

        return files


def create_backup(
        files: dict[Path, str],
        backup_directory: Path,
) -> tuple[set[Path], dict[Path, int]]:
        existing: set[Path] = set()
        modes: dict[Path, int] = {}

        for destination in files:
                if destination.is_symlink():
                        raise ValueError(
                                f"Refusing symlink destination: {destination}"
                        )

                if not destination.exists():
                        continue

                if not destination.is_file():
                        raise ValueError(
                                f"Destination is not a regular file: "
                                f"{destination}"
                        )

                backup_path = (
                        backup_directory
                        / destination.relative_to("/").as_posix()
                )
                backup_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                )
                shutil.copy2(destination, backup_path)

                existing.add(destination)
                modes[destination] = (
                        destination.stat().st_mode & 0o777
                )

        return existing, modes


def install_files(
        files: dict[Path, str],
        written: list[Path],
        modes: dict[Path, int],
) -> None:
        for destination, content in files.items():
                destination.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                )

                if destination.is_symlink():
                        raise ValueError(
                                f"Refusing symlink destination: {destination}"
                        )

                mode = modes.get(destination, 0o644)

                with tempfile.NamedTemporaryFile(
                        mode="w",
                        encoding="utf-8",
                        dir=destination.parent,
                        prefix=f".{destination.name}.",
                        suffix=".tmp",
                        delete=False,
                ) as temporary_file:
                        temporary_path = Path(temporary_file.name)
                        temporary_file.write(content)
                        temporary_file.flush()
                        os.fsync(temporary_file.fileno())

                os.chmod(temporary_path, mode)
                temporary_path.replace(destination)
                written.append(destination)


def restore_files(
        destinations: list[Path],
        existing: set[Path],
        backup_directory: Path,
        modes: dict[Path, int],
) -> list[str]:
        errors: list[str] = []

        for destination in reversed(destinations):
                try:
                        if destination in existing:
                                backup_path = (
                                        backup_directory
                                        / destination.relative_to("/").as_posix()
                                )

                                if not backup_path.is_file():
                                        raise FileNotFoundError(
                                                f"Missing backup: {backup_path}"
                                        )

                                shutil.copy2(
                                        backup_path,
                                        destination,
                                )
                                os.chmod(
                                        destination,
                                        modes.get(destination, 0o644),
                                )
                        else:
                                destination.unlink(missing_ok=True)

                except OSError as error:
                        errors.append(
                                f"Could not restore {destination}: {error}"
                        )

        return errors


def verify_deployment(zone_names: list[str]) -> list[str]:
        errors: list[str] = []

        active, output = run_command(
                ["systemctl", "is-active", SERVICE_NAME]
        )

        if not active or output.strip() != "active":
                errors.append(
                        "BIND is not active after reload: " + output
                )
                return errors

        for zone_name in zone_names:
                success, output = run_command(
                        [
                                "dig",
                                "+time=2",
                                "+tries=1",
                                "+short",
                                "@127.0.0.1",
                                zone_name,
                                "SOA",
                        ],
                        timeout=5.0,
                )

                if not success or not output.strip():
                        errors.append(
                                f"Zone {zone_name} failed SOA verification: "
                                f"{output}"
                        )

        return errors


def deploy(manifest_path: Path) -> int:
        if os.geteuid() != 0:
                raise PermissionError(
                        "The deployment helper must run as root."
                )

        files = load_manifest(manifest_path)

        BACKUP_ROOT.mkdir(
                parents=True,
                exist_ok=True,
                mode=0o700,
        )
        os.chmod(BACKUP_ROOT, 0o700)

        backup_directory = (
                BACKUP_ROOT
                / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        )
        backup_directory.mkdir(
                parents=True,
                exist_ok=False,
                mode=0o700,
        )

        existing, modes = create_backup(
                files,
                backup_directory,
        )

        written: list[Path] = []

        zone_names = [
                destination.name[3:]
                for destination in files
                if destination.parent == ZONE_DIRECTORY
                and destination.name.startswith("db.")
        ]

        try:
                install_files(files, written, modes)

                valid, output = run_command(
                        ["named-checkconf", "-z", str(CONFIG_PATH)]
                )

                if not valid:
                        raise RuntimeError(
                                "Candidate BIND validation failed:\n"
                                + output
                        )

                reloaded, output = run_command(
                        ["systemctl", "reload", SERVICE_NAME]
                )

                if not reloaded:
                        raise RuntimeError(
                                "BIND reload failed:\n" + output
                        )

                verification_errors = verify_deployment(zone_names)

                if verification_errors:
                        raise RuntimeError(
                                "Post-deployment verification failed:\n"
                                + "\n".join(verification_errors)
                        )

        except Exception as error:
                rollback_errors = restore_files(
                        written,
                        existing,
                        backup_directory,
                        modes,
                )

                restored, restore_output = run_command(
                        ["named-checkconf", "-z", str(CONFIG_PATH)]
                )

                reloaded, reload_output = run_command(
                        ["systemctl", "reload", SERVICE_NAME]
                )

                details = [
                        f"Deployment failed: {error}",
                        f"Restored configuration validates: {restored}",
                        f"Restored configuration check: {restore_output}",
                        f"Restored service reload succeeded: {reloaded}",
                        f"Restored service reload output: {reload_output}",
                ]
                details.extend(rollback_errors)

                raise RuntimeError("\n".join(details)) from error

        print(f"Deployment succeeded. Backup retained at {backup_directory}")
        return 0


def main() -> int:
        parser = argparse.ArgumentParser(
                description="Restricted BIND deployment helper."
        )
        parser.add_argument(
                "operation",
                choices=["install"],
        )
        parser.add_argument(
                "--manifest",
                required=True,
                type=Path,
        )
        arguments = parser.parse_args()

        return deploy(arguments.manifest)


if __name__ == "__main__":
        try:
                raise SystemExit(main())
        except Exception as error:
                print(f"Deployment failed: {error}")
                raise SystemExit(1)
