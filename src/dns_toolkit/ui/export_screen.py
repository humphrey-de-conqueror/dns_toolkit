from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Input, Select, Static

from dns_toolkit.repositories import ZoneRepository
from dns_toolkit.services.export_service import ExportService
from dns_toolkit.storage.settings_repository import SettingsRepository
from dns_toolkit.ui.navigation_screen import NavigationScreen


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
                with Vertical(id="export-page"):
                        yield Static(
                                "Export Zone",
                                classes="page-title",
                        )
                        yield Static(
                                "Export a zone file and a matching "
                                "BIND zone declaration."
                        )
                        yield Select(
                                [],
                                prompt="Select a zone",
                                id="export-zone",
                        )
                        yield Button(
                                "Refresh Zones",
                                id="refresh-export-zones",
                        )
                        yield Static("Output directory")
                        yield Input(id="export-directory")
                        yield Button(
                                "Export Selected Zone",
                                id="export-zone-button",
                                variant="primary",
                        )
                        yield Static(
                                "No export performed.",
                                id="export-status",
                        )

        def on_mount(self) -> None:
                settings = self.settings_repository.load()

                self.query_one(
                        "#export-directory",
                        Input,
                ).value = str(
                        Path(settings.export_directory).expanduser()
                )

                self.refresh_zones()

        def on_button_pressed(self, event: Button.Pressed) -> None:
                actions = {
                        "refresh-export-zones": self.refresh_zones,
                        "export-zone-button": self.export_selected_zone,
                }

                action = actions.get(event.button.id)

                if action is not None:
                        action()

        def refresh_zones(self) -> None:
                zones = self.zone_repository.list_zones()
                options = [
                        (zone.name, zone.name)
                        for zone in zones
                ]

                zone_select = self.query_one(
                        "#export-zone",
                        Select,
                )

                zone_select.set_options(options)

                self.query_one(
                        "#export-status",
                        Static,
                ).update(
                        f"Loaded {len(options)} saved zone(s)."
                )

        def export_selected_zone(self) -> None:
                selected = self.query_one(
                        "#export-zone",
                        Select,
                ).value

                if selected is Select.BLANK:
                        self.query_one(
                                "#export-status",
                                Static,
                        ).update("Select a zone before exporting.")
                        return

                output_text = self.query_one(
                        "#export-directory",
                        Input,
                ).value.strip()

                if not output_text:
                        self.query_one(
                                "#export-status",
                                Static,
                        ).update("Enter an output directory.")
                        return

                zone_name = str(selected)
                zone = self.zone_repository.get_zone(zone_name)

                if zone is None:
                        self.query_one(
                                "#export-status",
                                Static,
                        ).update(
                                "The selected zone no longer exists. "
                                "Refresh the zone list."
                        )
                        return

                output_directory = Path(output_text).expanduser()

                try:
                        exported_paths = self.export_service.export_zone(
                                zone=zone,
                                output_directory=output_directory,
                        )
                except (OSError, ValueError) as error:
                        self.query_one(
                                "#export-status",
                                Static,
                        ).update(f"Export failed: {error}")
                        return

                self.query_one(
                        "#export-status",
                        Static,
                ).update(
                        "Export completed:\n"
                        + "\n".join(
                                str(path)
                                for path in exported_paths
                        )
                )