
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Label, Static

from dns_toolkit.models import DNSRecord, Zone


class ZoneDetailsScreen(ModalScreen[DNSRecord | None]):
        CSS = """
        #dialog {
                width: 90%;
                height: 90%;
                max-height: 95%;
                border: round $primary;
                background: $surface;
                padding: 1 2;
                overflow-y: auto;
        }

        #zone-information {
                height: auto;
                margin-bottom: 1;
        }

        #record-table {
                height: 1fr;
                min-height: 8;
                margin-bottom: 1;
        }

        #actions {
                height: 3;
                align: right middle;
        }

        #actions Button {
                width: auto;
                min-width: 16;
        }

        .section-title {
                text-style: bold;
                color: $accent;
                margin-bottom: 1;
        }
        """

        BINDINGS = [
                ("escape", "dismiss_screen", "Close"),
        ]

        def __init__(self, zone: Zone) -> None:
                super().__init__()
                self.zone = zone

        def compose(self) -> ComposeResult:
                with Vertical(id="dialog"):
                        yield Static(
                                f"Zone Details: {self.zone.name}",
                                classes="section-title",
                        )

                        with Vertical(id="zone-information"):
                                yield Label(f"Zone: {self.zone.name}")
                                yield Label(
                                        f"Nameserver: {self.zone.nameserver}"
                                )
                                yield Label(
                                        f"Admin email: {self.zone.admin_email}"
                                )
                                yield Label(
                                        f"Zone type: {self.zone.zone_type.value}"
                                )

                        yield Static(
                                "DNS Records",
                                classes="section-title",
                        )

                        yield DataTable(id="record-table")

                        with Horizontal(id="actions"):
                                yield Button(
                                        "Delete Selected",
                                        variant="error",
                                        id="delete-record",
                                )
                                yield Button(
                                        "Close",
                                        id="close",
                                )

        def on_mount(self) -> None:
                table = self.query_one("#record-table", DataTable)
                table.add_columns("Name", "Type", "Value", "TTL")

                for index, record in enumerate(self.zone.records):
                        table.add_row(
                                record.name,
                                record.record_type,
                                record.value,
                                str(record.ttl),
                                key=str(index),
                        )

                table.cursor_type = "row"

        def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "close":
                        self.dismiss(None)
                        return

                if event.button.id == "delete-record":
                        self._delete_selected_record()

        def _delete_selected_record(self) -> None:
                table = self.query_one("#record-table", DataTable)

                if table.row_count == 0 or table.cursor_row is None:
                        self.notify(
                                "Select a record first.",
                                title="No Record Selected",
                                severity="warning",
                        )
                        return

                row_key, _ = table.coordinate_to_cell_key(
                        table.cursor_coordinate
                )
                record_index = int(row_key.value)
                self.dismiss(self.zone.records[record_index])

        def action_dismiss_screen(self) -> None:
                self.dismiss(None)
