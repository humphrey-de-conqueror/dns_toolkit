from pathlib import Path
from dns_toolkit.deployment.local_bind import LocalBindBackend
from dns_toolkit.deployment.base import DeploymentTarget
from dns_toolkit.storage.settings_repository import SettingsRepository


class TargetService:
        def __init__(
                self,
                settings_repository: SettingsRepository | None = None,
        ) -> None:
                self.settings_repository = (
                        settings_repository or SettingsRepository()
                )
                self._targets = {
                        "local": DeploymentTarget(
                                target_id="local",
                                name="Local BIND 9",
                                target_type="local",
                                host="localhost",
                        )
                }
                self._active_target_id = "local"

                settings = self.settings_repository.load()

                if settings.active_target_id in self._targets:
                        self._active_target_id = (
                                settings.active_target_id
                        )

        def list_targets(self) -> list[DeploymentTarget]:
                return list(self._targets.values())

        def get_active_target(self) -> DeploymentTarget:
                return self._targets[self._active_target_id]

        def select_target(self, target_id: str) -> DeploymentTarget:
                if target_id not in self._targets:
                        raise ValueError(
                                f"Unknown deployment target: {target_id}"
                        )

                self._active_target_id = target_id
                return self.get_active_target()

        def create_backend(self) -> LocalBindBackend:
                settings = self.settings_repository.load()
                target = self.get_active_target()

                if target.target_type != "local":
                        raise ValueError(
                                "Only local BIND deployment is supported."
                        )

                return LocalBindBackend(
			config_path=Path(settings.bind_config_path).expanduser(),
                        service_name=settings.bind_service_name,
                )
