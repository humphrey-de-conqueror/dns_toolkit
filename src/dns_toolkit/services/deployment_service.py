
from pathlib import Path

from dns_toolkit.deployment.base import (
        DeploymentBackend,
        DeploymentResult,
)


class DeploymentService:
        def __init__(self, backend: DeploymentBackend) -> None:
                self.backend = backend

        def inspect_target(self) -> dict[str, object]:
                return self.backend.inspect()

        def validate(
                self,
                config_path: Path,
        ) -> tuple[bool, str]:
                return self.backend.validate(config_path)

        def deploy(
                self,
                config_path: Path,
                zone_files: dict[Path, str],
                confirmed: bool,
        ) -> DeploymentResult:
                if not confirmed:
                        return DeploymentResult(
                                success=False,
                                message="Deployment cancelled by user.",
                                changed_files=[],
                        )

                return self.backend.deploy(
                        config_path=config_path,
                        zone_files=zone_files,
                        confirmed=True,
                )
