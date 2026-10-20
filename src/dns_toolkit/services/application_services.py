from pathlib import Path

from dns_toolkit.deployment.local_bind import LocalBindBackend
from dns_toolkit.repositories import ZoneRepository
from dns_toolkit.services.bind_service import BindService
from dns_toolkit.services.deployment_service import DeploymentService
from dns_toolkit.services.diagnostics_service import DiagnosticsService
from dns_toolkit.services.export_service import ExportService
from dns_toolkit.services.target_service import TargetService
from dns_toolkit.storage.settings_repository import SettingsRepository


class ApplicationServices:
        def __init__(self) -> None:
                self.settings_repository = SettingsRepository()
                self.zone_repository = ZoneRepository()
                self.export_service = ExportService()

                self.settings = self.settings_repository.load()
                self.refresh_settings()

        def refresh_settings(self) -> None:
                self.settings = self.settings_repository.load()

                self.bind_service = BindService(
                        service_name=self.settings.bind_service_name,
                )

                self.target_service = TargetService(
                        settings_repository=self.settings_repository,
                )

                backend = self.target_service.create_backend()

                self.deployment_service = DeploymentService(
                        backend=backend,
                )

                self.diagnostics_service = DiagnosticsService(
                        bind_service=self.bind_service,
                        backend=backend,
                        deployment_service=self.deployment_service,
                )

        def get_export_directory(self) -> Path:
                return Path(
                        self.settings.export_directory
                ).expanduser()