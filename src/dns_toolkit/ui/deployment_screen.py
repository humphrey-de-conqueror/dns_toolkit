
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Static

from dns_toolkit.bind_config import render_zone_file
from dns_toolkit.repositories import ZoneRepository
from dns_toolkit.services.deployment_service import DeploymentService
from dns_toolkit.storage.settings_repository import SettingsRepository


class DeploymentScreen(Screen):
        def __init__(
                self,
                deployment_service: DeploymentService,
                zone_repository: ZoneRepository,
                settings_repository: SettingsRepository,
        ) -> None:
                super().__init__()
                self.deployment_service = deployment_service
                self.zone_repository = zone_repository
                self.settings_repository = settings_repository

        def compose(self) -> ComposeResult:
                settings = self.settings_repository.load()

                with Vertical(id="deployment-page"):
                        yield Static("BIND Deployment", classes="page-title")
                        yield Static(
                                f"Configuration: {settings.bind_config_path}"
                        )
                        yield Static(
                                f"Zone directory: {settings.zone_file_directory}"
                        )
                        yield Static("", id="deployment-status")
                        yield Checkbox(
                                "I have reviewed this deployment and "
                                "authorize the changes.",
                                id="deployment-confirmation",
                        )
                        yield Button("Validate Configuration", id="validate")
                        yield Button("Deploy", id="deploy")
                        yield Button("Back", id="back")

        def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "validate":
                        self.validate_configuration()
                elif event.button.id == "deploy":
                        self.deploy()
                elif event.button.id == "back":
                        self.app.pop_screen()

        def validate_configuration(self) -> None:
                settings = self.settings_repository.load()
                config_path = Path(
                        settings.bind_config_path
                ).expanduser()

                success, message = self.deployment_service.validate(
                        config_path
                )

                status = "Validation passed." if success else "Validation failed."
                details = f"{status}\n{message}"

                self.query_one("#deployment-status", Static).update(details)

        def deploy(self) -> None:
                confirmation = self.query_one(
                        "#deployment-confirmation",
                        Checkbox,
                )

                if not confirmation.value:
                        self.query_one("#deployment-status", Static).update(
                                "Deployment cancelled: confirmation is required."
                        )
                        return

                settings = self.settings_repository.load()
                config_path = Path(
                        settings.bind_config_path
                ).expanduser()
                zone_directory = Path(
                        settings.zone_file_directory
                ).expanduser()

                zone_files = {}

                for zone in self.zone_repository.list_zones():
                        zone_path = (
                                zone_directory
                                / f"db.{zone.name.rstrip('.').lower()}"
                        )
                        zone_files[zone_path] = render_zone_file(zone)

                result = self.deployment_service.deploy(
                        config_path=config_path,
                        zone_files=zone_files,
                        confirmed=True,
                )

                self.query_one("#deployment-status", Static).update(
                        f"{'Success' if result.success else 'Failed'}: "
                        f"{result.message}"
                )
