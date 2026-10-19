
import shutil
import tempfile
from datetime import datetime
from pathlib import Path


class DeploymentFileManager:
        def __init__(
                self,
                backup_root: Path | None = None,
        ) -> None:
                self.backup_root = (
                        backup_root
                        or Path.home()
                        / ".local"
                        / "state"
                        / "dns-toolkit"
                        / "backups"
                )

        def install(
                self,
                files: dict[Path, str],
        ) -> Path:
                if not files:
                        raise ValueError("No files were provided for deployment.")

                backup_directory = (
                        self.backup_root
                        / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                )
                backup_directory.mkdir(parents=True, exist_ok=False)

                existing_files: set[Path] = set()
                installed_files: list[Path] = []

                try:
                        for destination in files:
                                destination.parent.mkdir(
                                        parents=True,
                                        exist_ok=True,
                                )

                                if destination.exists():
                                        if not destination.is_file():
                                                raise OSError(
                                                        "Deployment target is "
                                                        f"not a file: {destination}"
                                                )

                                        backup_path = (
                                                backup_directory
                                                / destination.as_posix().lstrip("/")
                                        )
                                        backup_path.parent.mkdir(
                                                parents=True,
                                                exist_ok=True,
                                        )
                                        shutil.copy2(
                                                destination,
                                                backup_path,
                                        )
                                        existing_files.add(destination)

                        for destination, content in files.items():
                                with tempfile.NamedTemporaryFile(
                                        mode="w",
                                        encoding="utf-8",
                                        dir=destination.parent,
                                        prefix=f".{destination.name}.",
                                        suffix=".tmp",
                                        delete=False,
                                ) as temporary_file:
                                        temporary_path = Path(
                                                temporary_file.name
                                        )
                                        temporary_file.write(content)
                                        temporary_file.flush()

                                temporary_path.replace(destination)
                                installed_files.append(destination)

                except Exception:
                        for destination in reversed(installed_files):
                                if destination in existing_files:
                                        backup_path = (
                                                backup_directory
                                                / destination.as_posix().lstrip("/")
                                        )
                                        if backup_path.exists():
                                                shutil.copy2(
                                                        backup_path,
                                                        destination,
                                                )
                                else:
                                        destination.unlink(missing_ok=True)

                        raise

                return backup_directory

        def restore(
                self,
                backup_directory: Path,
                destinations: list[Path],
        ) -> None:
                for destination in destinations:
                        backup_path = (
                                backup_directory
                                / destination.as_posix().lstrip("/")
                        )

                        if backup_path.exists():
                                destination.parent.mkdir(
                                        parents=True,
                                        exist_ok=True,
                                )
                                shutil.copy2(backup_path, destination)
                        else:
                                destination.unlink(missing_ok=True)
