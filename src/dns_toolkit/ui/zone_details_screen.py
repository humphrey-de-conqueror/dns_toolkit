
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Static

from dns_toolkit.models import Zone


class ZoneDetailsScreen(Screen):
        def __init__(self, zone: Zone) -> None:
                super().__init__()
                self.zone = zone

        def compose(self) -> ComposeResult:
                with Vertical(id="zone-details-page"):
                        yield Static(
                                f"Zone Details: {self.zone.name}",
                                classes="page-title",
                        )
                        yield Static(
                                f"Nameserver: {self.zone.nameserver}",
                                id="details-nameserver",
                        )
                        yield Static(
                                f"Administrator email: "
                                f"{self.zone.admin_email}",
                                id="details-admin-email",
                        )
                        yield Static(
                                f"Zone type: {self.zone.zone_type}",
                                id="details-zone-type",
                        )
                        yield Static("DNS Records", classes="section-title")
                        yield DataTable(id="details-records-table")
                        yield Static(
                                "This screen currently displays records. "
                                "Record editing will be connected next.",
                                id="details-status",
                        )
                        yield Button("Back", id="back-details")

        def on_mount(self) -> None:
                table = self.query_one(
                        "#details-records-table",
                        DataTable,
                )
                table.add_columns(
                        "Owner",
                        "Type",
                        "Value",
                        "TTL",
                )

                for record in self.zone.records:
                        table.add_row(
                                record.name,
                                record.record_type,
                                record.value,
                                str(record.ttl),
                        )

        def on_button_pressed(
                self,
                event: Button.Pressed,
        ) -> None:
                if event.button.id == "back-details":
                        self.app.pop_screen()
