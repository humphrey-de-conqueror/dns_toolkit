from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Vertical
from dns_toolkit.ui.navigation_screen import NavigationScreen
from textual.widgets import Button, Input, Static

from dns_toolkit.storage.settings_repository import (
        AppSettings,
        SettingsRepository,
)


class SettingsScreen(NavigationScreen):
        def __init__(
                self,
                settings_repository: SettingsRepository,
                on_saved: Callable[[], None] | None = None,
        ) -> None:
                super().__init__()
                self.settings_repository = settings_repository
                self.on_saved = on_saved

        def compose_page(self) -> ComposeResult:
                with Vertical(id="settings"):
                        yield Static(
                                "Settings",
                                classes="page-title",
                        )
                        yield Static("Active deployment target")
                        yield Input(id="setting-target")
                        yield Static("BIND configuration path")
                        yield Input(id="setting-config-path")
                        yield Static("BIND service name")
                        yield Input(id="setting-service-name")
                        yield Static("Zone file directory")
                        yield Input(id="setting-zone-directory")
                        yield Static("Default export directory")
                        yield Input(id="setting-export-directory")
                        yield Static("Default record TTL")
                        yield Input(
                                id="setting-default-ttl",
                        )

                        yield Static("", id="settings-message")

                        yield Button(
                                "Save Settings",
                                id="save-settings",
                                variant="primary",
                        )
                        yield Button(
                                "Reset Defaults",
                                id="reset-settings",
                        )
                        yield Button("Back", id="back-settings")

        def on_mount(self) -> None:
                self.load_settings()

        def load_settings(self) -> None:
                settings = self.settings_repository.load()

                values = {
                        "#setting-target": settings.active_target_id,
                        "#setting-config-path": settings.bind_config_path,
                        "#setting-service-name": settings.bind_service_name,
                        "#setting-zone-directory": (
                                settings.zone_file_directory
                        ),
                        "#setting-export-directory": (
                                settings.export_directory
                        ),
                        "#setting-default-ttl": str(
                                settings.default_ttl
                        ),
                }

                for selector, value in values.items():
                        self.query_one(selector, Input).value = value

        def on_button_pressed(self, event: Button.Pressed) -> None:
                actions = {
                        "save-settings": self.save_settings,
                        "reset-settings": self.reset_settings,
                        "back-settings": self.dismiss,
                }

                action = actions.get(event.button.id)

                if action is not None:
                        action()

        def save_settings(self) -> None:
                try:
                        ttl_text = self.query_one(
                                "#setting-default-ttl",
                                Input,
                        ).value.strip()

                        if not ttl_text.isdecimal():
                                raise ValueError(
                                        "Default TTL must be an integer."
                                )

                        settings = AppSettings(
                                active_target_id=self.query_one(
                                        "#setting-target",
                                        Input,
                                ).value.strip(),
                                bind_config_path=self.query_one(
                                        "#setting-config-path",
                                        Input,
                                ).value.strip(),
                                bind_service_name=self.query_one(
                                        "#setting-service-name",
                                        Input,
                                ).value.strip(),
                                zone_file_directory=self.query_one(
                                        "#setting-zone-directory",
                                        Input,
                                ).value.strip(),
                                export_directory=self.query_one(
                                        "#setting-export-directory",
                                        Input,
                                ).value.strip(),
                                default_ttl=int(ttl_text),
                        )

                        self.settings_repository.save(settings)

                except (ValueError, OSError) as error:
                        self.query_one(
                                "#settings-message",
                                Static,
                        ).update(f"Settings not saved: {error}")
                        return

                self.query_one(
                        "#settings-message",
                        Static,
                ).update("Settings saved.")

                if self.on_saved is not None:
                        self.on_saved()

                self.dismiss()

        def reset_settings(self) -> None:
                try:
                        self.settings_repository.reset()
                        self.load_settings()

                        if self.on_saved is not None:
                                self.on_saved()

                        self.query_one(
                                "#settings-message",
                                Static,
                        ).update("Default settings restored.")

                except (ValueError, OSError) as error:
                        self.query_one(
                                "#settings-message",
                                Static,
                        ).update(f"Could not reset settings: {error}")