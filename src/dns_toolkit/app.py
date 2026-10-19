
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
        Button,
        DataTable,
        Footer,
        Header,
        Label,
        ListItem,
        ListView,
        Static,
)

from dns_toolkit.models import DNSRecord, Zone
from dns_toolkit.repositories import ZoneRepository
from dns_toolkit.ui.add_record_screen import AddRecordScreen
from dns_toolkit.ui.add_zone_screen import AddZoneScreen
from dns_toolkit.ui.zone_details_screen import ZoneDetailsScreen
from dns_toolkit.ui.confirm_screen import ConfirmScreen


class DNSToolkitApp(App[None]):
        TITLE = "DNS Toolkit"
        SUB_TITLE = "Authoritative DNS Configuration"

        CSS = """
        Screen {
                layout: vertical;
        }

        #workspace {
                height: 1fr;
        }

        #sidebar {
                width: 24;
                border-right: solid $primary;
                padding: 1;
        }

        #sidebar-title {
                text-style: bold;
                color: $accent;
                margin-bottom: 1;
        }

        #content {
                width: 1fr;
                padding: 1 2;
                overflow-y: auto;
        }

        .section-title {
                text-style: bold;
                color: $accent;
                margin-bottom: 1;
        }

        #status {
                height: auto;
                border: round $primary;
                padding: 1;
                margin-bottom: 1;
        }

        #zone-actions {
                height: 3;
                align: left middle;
                margin-bottom: 1;
        }

        #zone-actions Static {
                width: 1fr;
        }

        #zone-actions Button {
                width: auto;
                min-width: 12;
                margin-right: 1;
        }

        #zone-table {
                height: 10;
                margin-bottom: 1;
        }

        #help {
                height: auto;
                color: $text-muted;
                margin-top: 1;
        }
        """

        BINDINGS = [
                ("q", "quit", "Quit"),
                ("question_mark", "help", "Help"),
        ]

        SECTIONS = [
                "Dashboard",
                "Zones",
                "Records",
                "Diagnostics",
                "Settings",
        ]

        def __init__(self) -> None:
                super().__init__()
                self.zone_repository = ZoneRepository()

        def compose(self) -> ComposeResult:
                yield Header()

                with Horizontal(id="workspace"):
                        with Vertical(id="sidebar"):
                                yield Label("NAVIGATION", id="sidebar-title")
                                yield ListView(
                                        *[
                                                ListItem(
                                                        Label(section),
                                                        id=f"nav-{section.lower()}",
                                                )
                                                for section in self.SECTIONS
                                        ],
                                        initial_index=0,
                                        id="navigation",
                                )

                        with Vertical(id="content"):
                                yield Static(
                                        "DNS TOOLKIT",
                                        classes="section-title",
                                        id="page-title",
                                )
                                yield Static(
                                        "Local BIND 9 | Configuration preview mode",
                                        id="status",
                                )

                                with Horizontal(id="zone-actions"):
                                        yield Static(
                                                "Configured zones",
                                                classes="section-title",
                                        )
                                        yield Button(
                                                "+ Add Zone",
                                                variant="primary",
                                                id="add-zone",
                                        )
                                        yield Button(
                                                "+ Add Record",
                                                id="add-record",
                                        )
                                        yield Button(
                                                "View Details",
                                                id="view-details",
                                        )
                                        yield Button(
                                                "Delete Zone",
                                                variant="error",
                                                id="delete-zone",
                                        )

                                yield DataTable(id="zone-table")
                                yield Static(
                                        "Select a zone row before adding a record.",
                                        id="page-description",
                                )
                                yield Static(
                                        "Preview-first | No system changes until explicitly applied",
                                        id="help",
                                )

                yield Footer()

        def on_mount(self) -> None:
                self._refresh_zone_table()

        def _refresh_zone_table(self) -> None:
                table = self.query_one("#zone-table", DataTable)
                table.clear(columns=True)
                table.add_columns("Zone", "Type", "Records", "Status")

                for zone in self.zone_repository.list_zones():
                        table.add_row(
                                zone.name,
                                zone.zone_type.value,
                                str(len(zone.records)),
                                "Draft",
                                key=zone.name,
                        )

                table.cursor_type = "row"

        def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "add-zone":
                        self.push_screen(
                                AddZoneScreen(),
                                self._handle_new_zone,
                        )
                elif event.button.id == "add-record":
                        self._open_add_record_screen()
                elif event.button.id == "view-details":
                        self._open_zone_details_screen()
                elif event.button.id == "delete-zone":
                        self._confirm_delete_zone()

        def _handle_new_zone(self, zone: Zone | None) -> None:
                if zone is None:
                        return

                try:
                        self.zone_repository.add_zone(zone)
                except (ValueError, RuntimeError) as exc:
                        self.notify(
                                str(exc),
                                title="Unable to Add Zone",
                                severity="error",
                        )
                        return

                self._refresh_zone_table()
                self.notify(
                        f"Zone '{zone.name}' added.",
                        title="Zone Created",
                )

        def _open_add_record_screen(self) -> None:
                table = self.query_one("#zone-table", DataTable)

                if table.row_count == 0:
                        self.notify(
                                "Create a zone before adding records.",
                                title="No Zones",
                                severity="warning",
                        )
                        return

                if table.cursor_row is None:
                        self.notify(
                                "Select a zone row first.",
                                title="No Zone Selected",
                                severity="warning",
                        )
                        return

                row_key, _ = table.coordinate_to_cell_key(
                        table.cursor_coordinate
                )
                zone = self.zone_repository.get_zone(str(row_key.value))

                if zone is None:
                        self.notify(
                                "The selected zone could not be found.",
                                title="Zone Not Found",
                                severity="error",
                        )
                        return

                self.push_screen(
                        AddRecordScreen(zone),
                        lambda record: self._handle_new_record(zone.name, record),
                )

        def _open_zone_details_screen(self) -> None:
                table = self.query_one("#zone-table", DataTable)

                if table.row_count == 0 or table.cursor_row is None:
                        self.notify(
                                "Select a zone row first.",
                                title="No Zone Selected",
                                severity="warning",
                        )
                        return

                row_key, _ = table.coordinate_to_cell_key(
                        table.cursor_coordinate
                )
                zone = self.zone_repository.get_zone(str(row_key.value))

                if zone is None:
                        self.notify(
                                "The selected zone could not be found.",
                                title="Zone Not Found",
                                severity="error",
                        )
                        return

                self.push_screen(
                        ZoneDetailsScreen(zone),
                        lambda record: self._handle_deleted_record(
                                zone.name,
                                record,
                        ),
                )

        def _handle_new_record(
                self,
                zone_name: str,
                record: DNSRecord | None,
        ) -> None:
                if record is None:
                        return

                try:
                        self.zone_repository.add_record(zone_name, record)
                except (ValueError, RuntimeError) as exc:
                        self.notify(
                                str(exc),
                                title="Unable to Add Record",
                                severity="error",
                        )
                        return

                self._refresh_zone_table()
                self.notify(
                        f"Record added to '{zone_name}'.",
                        title="Record Created",
                )

        def _handle_deleted_record(
                self,
                zone_name: str,
                record: DNSRecord | None,
        ) -> None:
                if record is None:
                        return

                try:
                        deleted = self.zone_repository.delete_record(
                                zone_name,
                                record,
                        )
                except (ValueError, RuntimeError) as exc:
                        self.notify(
                                str(exc),
                                title="Unable to Delete Record",
                                severity="error",
                        )
                        return

                if not deleted:
                        self.notify(
                                "The selected record no longer exists.",
                                title="Record Not Found",
                                severity="warning",
                        )
                        return

                self._refresh_zone_table()
                self.notify(
                        f"Record deleted from '{zone_name}'.",
                        title="Record Deleted",
                )

        def on_list_view_selected(
                self,
                event: ListView.Selected,
        ) -> None:
                if event.item.id is None:
                        return

                section = event.item.id.removeprefix("nav-")
                title = section.replace("_", " ").title()

                self.query_one("#page-title", Static).update(title)

                descriptions = {
                        "dashboard": "Overview of DNS Toolkit.",
                        "zones": "Create and inspect DNS zones.",
                        "records": (
                                "Select a zone and add A, AAAA, CNAME, MX, NS, "
                                "or TXT records."
                        ),
                        "diagnostics": (
                                "Inspect DNS responses and validate configurations."
                        ),
                        "settings": (
                                "Configure file paths and DNS backend options."
                        ),
                }

                self.query_one("#page-description", Static).update(
                        descriptions.get(
                                section,
                                "Section under development.",
                        )
                )

        def action_help(self) -> None:
                self.notify(
                        "Use the arrow keys to navigate. Press Enter to select. "
                        "Press Q to quit.",
                        title="DNS Toolkit Help",
                )


        def _confirm_delete_zone(self) -> None:
                table = self.query_one("#zone-table", DataTable)

                if table.row_count == 0 or table.cursor_row is None:
                        self.notify(
                                "Select a zone row first.",
                                title="No Zone Selected",
                                severity="warning",
                        )
                        return

                row_key, _ = table.coordinate_to_cell_key(
                        table.cursor_coordinate
                )
                zone_name = str(row_key.value)
                zone = self.zone_repository.get_zone(zone_name)

                if zone is None:
                        self.notify(
                                "The selected zone could not be found.",
                                title="Zone Not Found",
                                severity="error",
                        )
                        return

                message = (
                        f"Delete zone '{zone.name}' and all "
                        f"{len(zone.records)} of its DNS records?\n\n"
                        "This removes the zone from DNS Toolkit's saved "
                        "drafts. It does not modify system BIND 9 files."
                )

                self.push_screen(
                        ConfirmScreen(
                                title="Delete Zone?",
                                message=message,
                                confirm_label="Delete Zone",
                        ),
                        lambda confirmed: self._handle_delete_zone(
                                zone.name,
                                confirmed,
                        ),
                )

        def _handle_delete_zone(
                self,
                zone_name: str,
                confirmed: bool,
        ) -> None:
                if not confirmed:
                        return

                try:
                        deleted = self.zone_repository.delete_zone(zone_name)
                except (ValueError, RuntimeError) as exc:
                        self.notify(
                                str(exc),
                                title="Unable to Delete Zone",
                                severity="error",
                        )
                        return

                if not deleted:
                        self.notify(
                                f"Zone '{zone_name}' no longer exists.",
                                title="Zone Not Found",
                                severity="warning",
                        )
                        return

                self._refresh_zone_table()
                self.notify(
                        f"Zone '{zone_name}' and its records were deleted.",
                        title="Zone Deleted",
                )

