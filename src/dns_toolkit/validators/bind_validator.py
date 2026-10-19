
import shutil
import subprocess
from pathlib import Path


class BindValidator:
        def validate_configuration(
                self,
                config_path: Path,
        ) -> tuple[bool, str]:
                executable = shutil.which("named-checkconf")

                if executable is None:
                        return False, "named-checkconf is not installed."

                result = subprocess.run(
                        [executable, str(config_path)],
                        capture_output=True,
                        text=True,
                        check=False,
                )

                output = "\n".join(
                        part
                        for part in (result.stdout, result.stderr)
                        if part
                )

                return (
                        result.returncode == 0,
                        output or "Configuration syntax is valid.",
                )

        def validate_zone_file(
                self,
                zone_name: str,
                zone_file_path: Path,
        ) -> tuple[bool, str]:
                executable = shutil.which("named-checkzone")

                if executable is None:
                        return False, "named-checkzone is not installed."

                result = subprocess.run(
                        [
                                executable,
                                zone_name,
                                str(zone_file_path),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                )

                output = "\n".join(
                        part
                        for part in (result.stdout, result.stderr)
                        if part
                )

                return (
                        result.returncode == 0,
                        output or "Zone-file validation completed.",
                )
