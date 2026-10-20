
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from dns_toolkit.ui.navigation_screen import NavigationScreen
from textual.widgets import Button, DataTable, Static

from dns_toolkit.models import Zone
from dns_toolkit.repositories import ZoneRepository
from dns_toolkit.ui.add_zone_screen import AddZoneScreen
from dns_toolkit.ui.bind_preview_screen import BindPreviewScreen
from dns_toolkit.ui.confirm_screen import ConfirmScreen
from dns_toolkit.ui.zone_details_screen import ZoneDetailsScreen


class ZonesScreen(NavigationScreen):
        def __init__(self, zone_repository: ZoneRepository) -> None:
                super().__init__()
                self.zone_repository = zone_repository

        def compose_page(self) -> ComposeResult:
                with Vertical(id="zones-page"):
                        yield Static("DNS Zones", classes="page-title")
                        yield DataTable(id="zones-table")
                        with Horizontal():
                                yield Button("Add Zone", id="add-zone")
                                yield Button("View Details", id="details")
                                yield Button("Preview BIND", id="preview")
                                yield Button("Delete Zone", id="delete")
                        yield Button("Refresh", id="refresh")
                        yield Button("Back", id="back")

        def on_mount(self) -> None:
                table = self.query_one("#zones-table", DataTable)
                table.add_columns("Zone", "Nameserver", "Admin Email", "Records")
                self.refresh_zones()

        def refresh_zones(self) -> None:
                table = self.query_one("#zones-table", DataTable)
                table.clear()

                for zone in self.zone_repository.list_zones():
                        table.add_row(
                                zone.name,
                                zone.nameserver,
                                zone.admin_email,
                                str(len(zone.records)),
                                key=zone.name,
                        )

        def _selected_zone(self):
                table = self.query_one("#zones-table", DataTable)

                if table.row_count == 0:
                        return None

                cell_key = table.coordinate_to_cell_key(
                        table.cursor_coordinate
                )
                zone_name = str(cell_key.row_key.value)

                return self.zone_repository.get_zone(zone_name)

        def on_button_pressed(self, event: Button.Pressed) -> None:
                actions = {
                        "add-zone": self.add_zone,
                        "details": self.view_details,
                        "preview": self.preview_zone,
                        "delete": self.delete_zone,
                        "refresh": self.refresh_zones,
                        "back": self.app.pop_screen,
                }

                action = actions.get(event.button.id)

                if action is not None:
                        action()

        def add_zone(self) -> None:
                self.app.push_screen(
                        AddZoneScreen(),
                        self._on_zone_created,
                )

        def _on_zone_created(self, zone: Zone | None) -> None:
                if zone is None:
                        return

                self.zone_repository.add_zone(zone)
                self.refresh_zones()

        def view_details(self) -> None:
                zone = self._selected_zone()

                if zone is not None:
                        self.app.push_screen(
                                ZoneDetailsScreen(zone),
                                self._on_details_closed,
                        )

        def _on_details_closed(self, result: object) -> None:
                self.refresh_zones()

        def preview_zone(self) -> None:
                zone = self._selected_zone()

                if zone is not None:
                        self.app.push_screen(BindPreviewScreen(zone))

        def delete_zone(self) -> None:
                zone = self._selected_zone()

                if zone is None:
                        return

                self.app.push_screen(
                        ConfirmScreen(
                                f"Delete zone {zone.name}? "
                                "This cannot be undone."
                        ),
                        lambda confirmed: self._on_delete_confirmed(
                                zone.name,
                                confirmed,
                        ),
                )

        def _on_delete_confirmed(
                self,
                zone_name: str,
                confirmed: bool | None,
        ) -> None:
                if confirmed:
                        self.zone_repository.delete_zone(zone_name)

                self.refresh_zones()
