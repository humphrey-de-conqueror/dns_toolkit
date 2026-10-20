
from dns_toolkit.deployment.local_bind import LocalBindBackend
from dns_toolkit.services.bind_service import BindService
from dns_toolkit.services.deployment_service import DeploymentService


class DiagnosticsService:
        def __init__(
                self,
                bind_service: BindService,
                backend: LocalBindBackend,
                deployment_service: DeploymentService | None = None,
        ) -> None:
                self.bind_service = bind_service
                self.backend = backend
                self.deployment_service = deployment_service

        def collect(self) -> dict[str, object]:
                diagnostics: dict[str, object] = {
                        "executables": self.bind_service.get_executables(),
                        "service": self.bind_service.get_service_status(),
                        "environment": self.backend.inspect(),
                }

                if self.deployment_service is not None:
                        ready, message = (
                                self.deployment_service.preflight()
                        )
                        diagnostics["deployment_preflight"] = {
                                "ready": ready,
                                "message": message,
                        }

                return diagnostics

        def validate_configuration(
                self,
                config_path,
        ) -> tuple[bool, str]:
                return self.backend.validate(config_path)
