
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from dns_toolkit.storage.settings_repository import (
        AppSettings,
        SettingsRepository,
)


class SettingsScreen(Screen):
        def __init__(
                self,
                settings_repository: SettingsRepository,
        ) -> None:
                super().__init__()
                self.settings_repository = settings_repository

        def compose(self) -> ComposeResult:
                settings = self.settings_repository.load()

                with Vertical(id="settings"):
                        yield Static("Settings", classes="page-title")

                        yield Label("Active target ID")
                        yield Input(
                                value=settings.active_target_id,
                                id="active-target",
                        )

                        yield Label("BIND configuration path")
                        yield Input(
                                value=settings.bind_config_path,
                                id="bind-config",
                        )

                        yield Label("BIND service name")
                        yield Input(
                                value=settings.bind_service_name,
                                id="service-name",
                        )

                        yield Label("Zone-file directory")
                        yield Input(
                                value=settings.zone_file_directory,
                                id="zone-directory",
                        )

                        yield Label("Export directory")
                        yield Input(
                                value=settings.export_directory,
                                id="export-directory",
                        )

                        yield Label("Default TTL")
                        yield Input(
                                value=str(settings.default_ttl),
                                id="default-ttl",
                        )

                        yield Button("Save Settings", id="save")
                        yield Button("Reset Defaults", id="reset")
                        yield Static("", id="settings-message")
                        yield Button("Back", id="back")

        def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "save":
                        self.save_settings()
                elif event.button.id == "reset":
                        self.reset_settings()
                elif event.button.id == "back":
                        self.app.pop_screen()

        def save_settings(self) -> None:
                try:
                        default_ttl = int(
                                self.query_one("#default-ttl", Input).value
                        )

                        settings = AppSettings(
                                active_target_id=self.query_one(
                                        "#active-target", Input
                                ).value.strip(),
                                bind_config_path=self.query_one(
                                        "#bind-config", Input
                                ).value.strip(),
                                bind_service_name=self.query_one(
                                        "#service-name", Input
                                ).value.strip(),
                                zone_file_directory=self.query_one(
                                        "#zone-directory", Input
                                ).value.strip(),
                                export_directory=self.query_one(
                                        "#export-directory", Input
                                ).value.strip(),
                                default_ttl=default_ttl,
                        )

                        self.settings_repository.save(settings)
                        message = "Settings saved."
                except (ValueError, OSError) as error:
                        message = f"Could not save settings: {error}"

                self.query_one("#settings-message", Static).update(message)

        def reset_settings(self) -> None:
                self.settings_repository.reset()
                self.app.pop_screen()
                self.app.push_screen(
                        SettingsScreen(self.settings_repository)
                )
