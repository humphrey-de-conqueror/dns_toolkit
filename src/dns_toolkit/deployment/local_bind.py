
import shutil
import subprocess
from pathlib import Path

from dns_toolkit.deployment.base import (
        DeploymentBackend,
        DeploymentResult,
)


class LocalBindBackend(DeploymentBackend):
        def __init__(
                self,
                config_path: Path = Path("/etc/bind/named.conf"),
                service_name: str = "bind9",
        ) -> None:
                self.config_path = config_path
                self.service_name = service_name

        def inspect(self) -> dict[str, object]:
                return {
                        "platform": "local-linux",
                        "config_path": str(self.config_path),
                        "bind_available": shutil.which("named") is not None,
                        "checkconf_available": (
                                shutil.which("named-checkconf") is not None
                        ),
                        "checkzone_available": (
                                shutil.which("named-checkzone") is not None
                        ),
                        "systemctl_available": (
                                shutil.which("systemctl") is not None
                        ),
                }

        def validate(self, config_path: Path) -> tuple[bool, str]:
                checker = shutil.which("named-checkconf")

                if checker is None:
                        return False, "named-checkconf is not installed."

                result = subprocess.run(
                        [checker, str(config_path)],
                        capture_output=True,
                        text=True,
                        check=False,
                )

                output = "\n".join(
                        part
                        for part in (result.stdout, result.stderr)
                        if part
                )

                return result.returncode == 0, output or "Validation completed."

        def deploy(
                self,
                config_path: Path,
                zone_files: dict[Path, str],
                confirmed: bool,
        ) -> DeploymentResult:
                if not confirmed:
                        return DeploymentResult(
                                success=False,
                                message="Deployment was not confirmed.",
                                changed_files=[],
                        )

                return DeploymentResult(
                        success=False,
                        message=(
                                "Deployment is not implemented yet. "
                                "The file transaction, privileged writes, "
                                "backup, and service activation workflow "
                                "must be implemented before deployment "
                                "can modify system files."
                        ),
                        changed_files=[],
                )
