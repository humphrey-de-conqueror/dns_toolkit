
from textual.app import ComposeResult
from textual.containers import Vertical
from dns_toolkit.ui.navigation_screen import NavigationScreen
from textual.widgets import Button, DataTable, Static

from dns_toolkit.repositories import ZoneRepository
from dns_toolkit.ui.zone_details_screen import ZoneDetailsScreen


class RecordsScreen(NavigationScreen):
        def __init__(self, zone_repository: ZoneRepository) -> None:
                super().__init__()
                self.zone_repository = zone_repository
                self.zone_names_by_key: dict[str, str] = {}

        def compose_page(self) -> ComposeResult:
                with Vertical(id="records-page"):
                        yield Static("DNS Records", classes="page-title")
                        yield DataTable(id="records-table")
                        yield Button("Open Zone Details", id="details")
                        yield Button("Refresh", id="refresh")
                        yield Button("Back", id="back")

        def on_mount(self) -> None:
                table = self.query_one("#records-table", DataTable)
                table.add_columns(
                        "Zone",
                        "Owner",
                        "Type",
                        "Value",
                        "TTL",
                )
                self.refresh_records()

        def refresh_records(self) -> None:
                table = self.query_one("#records-table", DataTable)
                table.clear()
                self.zone_names_by_key.clear()

                for zone in self.zone_repository.list_zones():
                        for index, record in enumerate(zone.records):
                                row_key = f"{zone.name}:{index}"
                                self.zone_names_by_key[row_key] = zone.name

                                table.add_row(
                                        zone.name,
                                        record.name,
                                        record.record_type,
                                        record.value,
                                        str(record.ttl),
                                        key=row_key,
                                )

        def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "refresh":
                        self.refresh_records()
                elif event.button.id == "details":
                        self.open_selected_zone()
                elif event.button.id == "back":
                        self.app.pop_screen()

        def open_selected_zone(self) -> None:
                table = self.query_one("#records-table", DataTable)

                if table.row_count == 0 or table.cursor_row is None:
                        return

                cell_key = table.coordinate_to_cell_key(
                        table.cursor_coordinate
                )
                row_key = str(cell_key.row_key.value)
                zone_name = self.zone_names_by_key.get(row_key)

                if zone_name is None:
                        return

                zone = self.zone_repository.get_zone(zone_name)

                if zone is not None:
                        self.app.push_screen(ZoneDetailsScreen(zone))
