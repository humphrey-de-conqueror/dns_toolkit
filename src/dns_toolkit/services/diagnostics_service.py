
from pathlib import Path

from dns_toolkit.deployment.base import DeploymentBackend
from dns_toolkit.services.bind_service import BindService


class DiagnosticsService:
        def __init__(
                self,
                bind_service: BindService,
                backend: DeploymentBackend,
        ) -> None:
                self.bind_service = bind_service
                self.backend = backend

        def collect(self) -> dict[str, object]:
                return {
                        "executables": self.bind_service.get_executables(),
                        "service": self.bind_service.get_service_status(),
                        "environment": self.backend.inspect(),
                }

        def validate_configuration(
                self,
                config_path: Path,
        ) -> tuple[bool, str]:
                return self.backend.validate(config_path)
