
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Input, Select, Static

from dns_toolkit.models import DNSRecord
from dns_toolkit.repositories import ZoneRepository


class ZoneDetailsScreen(Screen):
        RECORD_TYPES = [
                ("A", "A"),
                ("AAAA", "AAAA"),
                ("CNAME", "CNAME"),
                ("MX", "MX"),
                ("NS", "NS"),
                ("PTR", "PTR"),
                ("TXT", "TXT"),
                ("SRV", "SRV"),
        ]

        def __init__(
                self,
                zone_name: str,
                zone_repository: ZoneRepository,
        ) -> None:
                super().__init__()
                self.zone_name = zone_name
                self.zone_repository = zone_repository
                self.selected_record_index: int | None = None

        def compose(self) -> ComposeResult:
                with Vertical(id="zone-details-page"):
                        yield Static(
                                f"Zone Details: {self.zone_name}",
                                classes="page-title",
                        )
                        yield Static("", id="details-metadata")
                        yield DataTable(id="details-records-table")

                        yield Static(
                                "Record editor",
                                classes="section-title",
                        )
                        yield Static("Owner name (e.g. www or @)")
                        yield Input(
                                placeholder="@",
                                id="record-name",
                        )
                        yield Static("Record type")
                        yield Select(
                                self.RECORD_TYPES,
                                value="A",
                                id="record-type",
                        )
                        yield Static("Record value")
                        yield Input(
                                placeholder="192.0.2.10",
                                id="record-value",
                        )
                        yield Static("TTL in seconds")
                        yield Input(
                                value="3600",
                                id="record-ttl",
                                input_type="integer",
                        )

                        with Horizontal():
                                yield Button(
                                        "Add Record",
                                        id="add-record",
                                        variant="primary",
                                )
                                yield Button(
                                        "Load Selected",
                                        id="load-record",
                                )
                                yield Button(
                                        "Update Selected",
                                        id="update-record",
                                )
                                yield Button(
                                        "Delete Selected",
                                        id="delete-record",
                                        variant="error",
                                )

                        yield Static("", id="details-status")
                        yield Button("Back", id="back-details")

        def on_mount(self) -> None:
                table = self.query_one(
                        "#details-records-table",
                        DataTable,
                )
                table.add_columns("Owner", "Type", "Value", "TTL")
                self.refresh_zone()

        def on_button_pressed(
                self,
                event: Button.Pressed,
        ) -> None:
                actions = {
                        "add-record": self.add_record,
                        "load-record": self.load_selected_record,
                        "update-record": self.update_record,
                        "delete-record": self.delete_record,
                        "back-details": self.dismiss,
                }

                action = actions.get(event.button.id)

                if action is not None:
                        action()

        def refresh_zone(self) -> None:
                zone = self.zone_repository.get_zone(self.zone_name)

                if zone is None:
                        self.query_one(
                                "#details-metadata",
                                Static,
                        ).update("This zone no longer exists.")
                        self.query_one(
                                "#details-records-table",
                                DataTable,
                        ).clear()
                        return

                self.query_one(
                        "#details-metadata",
                        Static,
                ).update(
                        f"Nameserver: {zone.nameserver}\n"
                        f"Administrator email: {zone.admin_email}\n"
                        f"Zone type: {zone.zone_type}"
                )

                table = self.query_one(
                        "#details-records-table",
                        DataTable,
                )
                table.clear()

                for index, record in enumerate(zone.records):
                        table.add_row(
                                record.name,
                                record.record_type,
                                record.value,
                                str(record.ttl),
                                key=str(index),
                        )

        def _selected_record_index(self) -> int | None:
                table = self.query_one(
                        "#details-records-table",
                        DataTable,
                )

                if table.row_count == 0:
                        return None

                cell_key = table.coordinate_to_cell_key(
                        table.cursor_coordinate
                )

                try:
                        return int(cell_key.row_key.value)
                except (TypeError, ValueError):
                        return None

        def _read_record_fields(self) -> DNSRecord:
                name = self.query_one("#record-name", Input).value.strip()
                record_type = self.query_one(
                        "#record-type",
                        Select,
                ).value
                value = self.query_one(
                        "#record-value",
                        Input,
                ).value.strip()
                ttl_text = self.query_one("#record-ttl", Input).value.strip()

                if not name:
                        raise ValueError("Record owner name is required.")

                if record_type is Select.BLANK:
                        raise ValueError("Select a record type.")

                if not value:
                        raise ValueError("Record value is required.")

                if not ttl_text.isdecimal():
                        raise ValueError("TTL must be a positive integer.")

                ttl = int(ttl_text)

                if ttl < 1 or ttl > 2147483647:
                        raise ValueError(
                                "TTL must be between 1 and 2147483647."
                        )

                return DNSRecord(
                        name=name,
                        record_type=str(record_type),
                        value=value,
                        ttl=ttl,
                )

        def _show_status(self, message: str) -> None:
                self.query_one(
                        "#details-status",
                        Static,
                ).update(message)

        def _clear_editor(self) -> None:
                self.query_one("#record-name", Input).value = ""
                self.query_one("#record-type", Select).value = "A"
                self.query_one("#record-value", Input).value = ""
                self.query_one("#record-ttl", Input).value = "3600"
                self.selected_record_index = None

        def add_record(self) -> None:
                try:
                        record = self._read_record_fields()
                        self.zone_repository.add_record(
                                self.zone_name,
                                record,
                        )
                except (ValueError, OSError) as error:
                        self._show_status(f"Could not add record: {error}")
                        return

                self.refresh_zone()
                self._clear_editor()
                self._show_status("Record added and saved.")

        def load_selected_record(self) -> None:
                index = self._selected_record_index()

                if index is None:
                        self._show_status("Select a record first.")
                        return

                zone = self.zone_repository.get_zone(self.zone_name)

                if zone is None or index >= len(zone.records):
                        self._show_status(
                                "The selected record no longer exists."
                        )
                        self.refresh_zone()
                        return

                record = zone.records[index]
                self.selected_record_index = index

                self.query_one("#record-name", Input).value = record.name
                self.query_one("#record-type", Select).value = (
                        record.record_type
                )
                self.query_one("#record-value", Input).value = record.value
                self.query_one("#record-ttl", Input).value = str(record.ttl)

                self._show_status(
                        f"Loaded record {record.name} for editing."
                )

        def update_record(self) -> None:
                index = self.selected_record_index

                if index is None:
                        self._show_status(
                                "Use Load Selected before updating a record."
                        )
                        return

                try:
                        record = self._read_record_fields()
                        self.zone_repository.update_record(
                                self.zone_name,
                                index,
                                record,
                        )
                except (ValueError, IndexError, OSError) as error:
                        self._show_status(
                                f"Could not update record: {error}"
                        )
                        return

                self.refresh_zone()
                self._clear_editor()
                self._show_status("Record updated and saved.")

        def delete_record(self) -> None:
                index = self._selected_record_index()

                if index is None:
                        self._show_status("Select a record first.")
                        return

                try:
                        self.zone_repository.delete_record(
                                self.zone_name,
                                index,
                        )
                except (ValueError, IndexError, OSError) as error:
                        self._show_status(
                                f"Could not delete record: {error}"
                        )
                        return

                self.refresh_zone()
                self._clear_editor()
                self._show_status("Record deleted and saved.")
