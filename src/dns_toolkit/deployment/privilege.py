
import shutil
import subprocess
from pathlib import Path


class PrivilegeManager:
        ALLOWED_OPERATIONS = {
                "install",
                "restore",
                "reload",
                "validate",
        }

        def __init__(self, helper_path: Path) -> None:
                self.helper_path = helper_path

        def is_available(self) -> bool:
                return (
                        shutil.which("pkexec") is not None
                        and self.helper_path.is_file()
                        and self.helper_path.is_absolute()
                )

        def run(
                self,
                operation: str,
                arguments: list[str],
        ) -> tuple[bool, str]:
                if operation not in self.ALLOWED_OPERATIONS:
                        return False, f"Unsupported operation: {operation}"

                pkexec = shutil.which("pkexec")

                if pkexec is None:
                        return False, "pkexec is not installed."

                if not self.helper_path.is_absolute():
                        return False, "The privileged helper path must be absolute."

                if not self.helper_path.is_file():
                        return False, "The privileged helper is not installed."

                result = subprocess.run(
                        [
                                pkexec,
                                str(self.helper_path),
                                operation,
                                *arguments,
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
                        output or f"Privileged operation exited with {result.returncode}.",
                )
