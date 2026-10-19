
import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


CONFIG_PATH = Path("/etc/bind/named.conf")
INCLUDE_PATH = Path("/etc/bind/dns-toolkit-zones.conf")
ZONE_DIRECTORY = Path("/etc/bind/zones")
BACKUP_ROOT = Path("/var/lib/dns-toolkit/backups")
SERVICE_NAME = "bind9"


def validate_destination(destination: Path) -> None:
        if destination == CONFIG_PATH:
                return

        if destination == INCLUDE_PATH:
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


def run_command(command: list[str]) -> tuple[bool, str]:
        try:
                result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=30,
                )
        except (OSError, subprocess.TimeoutExpired) as error:
                return False, str(error)

        output = "\n".join(
                part
                for part in (result.stdout, result.stderr)
                if part
        )

        return result.returncode == 0, output


def load_manifest(path: Path) -> dict[Path, str]:
        payload = json.loads(path.read_text(encoding="utf-8"))

        if payload.get("version") != 1:
                raise ValueError("Unsupported manifest version.")

        if Path(payload.get("config_path", "")) != CONFIG_PATH:
                raise ValueError("Unexpected BIND configuration path.")

        if payload.get("service_name") != SERVICE_NAME:
                raise ValueError("Unexpected service name.")

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

        if CONFIG_PATH not in files:
                raise ValueError(
                        "Manifest must contain the candidate named.conf."
                )

        if INCLUDE_PATH not in files:
                raise ValueError(
                        "Manifest must contain the managed zone include."
                )

        return files


def create_backup(
        files: dict[Path, str],
        backup_directory: Path,
) -> set[Path]:
        existing: set[Path] = set()

        for destination in files:
                if destination.is_symlink():
                        raise ValueError(
                                f"Refusing symlink destination: {destination}"
                        )

                if destination.exists():
                        if not destination.is_file():
                                raise ValueError(
                                        f"Not a regular file: {destination}"
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

        return existing


def write_files(files: dict[Path, str]) -> list[Path]:
        written: list[Path] = []

        for destination, content in files.items():
                destination.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                )

                if destination.is_symlink():
                        raise ValueError(
                                f"Refusing symlink destination: {destination}"
                        )

                old_mode = (
                        destination.stat().st_mode & 0o777
                        if destination.exists()
                        else 0o644
                )

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

                os.chmod(temporary_path, old_mode)
                temporary_path.replace(destination)
                written.append(destination)

        return written


def restore_files(
        destinations: list[Path],
        existing: set[Path],
        backup_directory: Path,
) -> None:
        for destination in reversed(destinations):
                if destination in existing:
                        backup_path = (
                                backup_directory
                                / destination.relative_to("/").as_posix()
                        )
                        shutil.copy2(backup_path, destination)
                else:
                        destination.unlink(missing_ok=True)


def install(manifest_path: Path) -> int:
        if os.geteuid() != 0:
                raise PermissionError(
                        "The deployment helper must run as root."
                )

        files = load_manifest(manifest_path)

        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(
                prefix="dns-toolkit-backup-",
                dir=BACKUP_ROOT,
        ) as temporary_backup:
                backup_directory = Path(temporary_backup)
                existing = create_backup(files, backup_directory)
                written: list[Path] = []

                try:
                        written = write_files(files)

                        valid, output = run_command(
                                ["named-checkconf", str(CONFIG_PATH)]
                        )

                        if not valid:
                                raise RuntimeError(
                                        "BIND configuration validation failed:\n"
                                        + output
                                )

                        reloaded, output = run_command(
                                ["systemctl", "reload", SERVICE_NAME]
                        )

                        if not reloaded:
                                raise RuntimeError(
                                        "BIND reload failed:\n" + output
                                )

                except Exception:
                        restore_files(
                                written,
                                existing,
                                backup_directory,
                        )
                        run_command(
                                ["systemctl", "reload", SERVICE_NAME]
                        )
                        raise

        print("Deployment completed and BIND reload succeeded.")
        return 0


def main() -> int:
        parser = argparse.ArgumentParser(
                description="Restricted DNS Toolkit BIND deployment helper."
        )
        parser.add_argument(
                "operation",
                choices=["install"],
        )
        parser.add_argument("--manifest", required=True, type=Path)
        arguments = parser.parse_args()

        if arguments.operation != "install":
                raise ValueError("Unsupported operation.")

        return install(arguments.manifest)


if __name__ == "__main__":
        try:
                raise SystemExit(main())
        except Exception as error:
                print(f"Deployment failed: {error}")
                raise SystemExit(1)
