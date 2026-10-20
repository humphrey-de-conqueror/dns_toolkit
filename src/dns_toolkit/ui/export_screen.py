
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from dns_toolkit.ui.navigation_screen import NavigationScreen
from textual.widgets import Button, Input, Select, Static

from dns_toolkit.repositories import ZoneRepository
from dns_toolkit.services.export_service import ExportService
from dns_toolkit.storage.settings_repository import SettingsRepository


class ExportScreen(NavigationScreen):
        def __init__(
                self,
                export_service: ExportService,
                zone_repository: ZoneRepository,
                settings_repository: SettingsRepository,
        ) -> None:
                super().__init__()
                self.export_service = export_service
                self.zone_repository = zone_repository
                self.settings_repository = settings_repository

        def compose_page(self) -> ComposeResult:
                zones = self.zone_repository.list_zones()
                options = [
                        (zone.name, zone.name)
                        for zone in zones
                ]
                settings = self.settings_repository.load()

                with Vertical(id="export-page"):
                        yield Static(
                                "Export BIND Configuration",
                                classes="page-title",
                        )
                        yield Static(
                                "Export creates files in the selected "
                                "directory. It does not deploy them."
                        )
                        yield Static("Select zone")
                        yield Select(
                                options,
                                prompt="Choose a zone",
                                id="export-zone",
                        )
                        yield Static("Output directory")
                        yield Input(
                                value=str(
                                        Path(
                                                settings.export_directory
                                        ).expanduser()
                                ),
                                id="export-directory",
                                placeholder="Output directory",
                        )
                        yield Button("Export", id="export")
                        yield Static("", id="export-status")
                        yield Button("Back", id="back")

        def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "export":
                        self.export_selected_zone()
                elif event.button.id == "back":
                        self.app.pop_screen()

        def export_selected_zone(self) -> None:
                selected = self.query_one(
                        "#export-zone",
                        Select,
                ).value

                if selected is Select.BLANK:
                        self.show_status("Select a zone to export.")
                        return

                output_value = self.query_one(
                        "#export-directory",
                        Input,
                ).value.strip()

                if not output_value:
                        self.show_status("Output directory cannot be empty.")
                        return

                zone = self.zone_repository.get_zone(str(selected))

                if zone is None:
                        self.show_status("The selected zone no longer exists.")
                        return

                try:
                        output_directory = Path(
                                output_value
                        ).expanduser()

                        files = self.export_service.export_zone(
                                zone,
                                output_directory,
                        )

                        file_list = "\n".join(
                                str(path) for path in files
                        )
                        self.show_status(
                                f"Export completed:\n{file_list}"
                        )
                except (OSError, ValueError) as error:
                        self.show_status(f"Export failed: {error}")

        def show_status(self, message: str) -> None:
                self.query_one("#export-status", Static).update(message)
