
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from dns_toolkit.models import Zone, ZoneType


class AddZoneScreen(Screen):
        def compose(self) -> ComposeResult:
                with Vertical(id="add-zone-page"):
                        yield Static("Add DNS Zone", classes="page-title")

                        yield Static("Zone name")
                        yield Input(
                                placeholder="example.com",
                                id="zone-name",
                        )

                        yield Static("Primary nameserver")
                        yield Input(
                                value="ns1.example.com.",
                                id="zone-nameserver",
                        )

                        yield Static("Administrator email")
                        yield Input(
                                value="hostmaster@example.com",
                                id="zone-admin-email",
                        )

                        yield Static("", id="add-zone-status")

                        yield Button(
                                "Create Zone",
                                id="create-zone",
                                variant="primary",
                        )
                        yield Button("Cancel", id="cancel-zone")

        def on_button_pressed(
                self,
                event: Button.Pressed,
        ) -> None:
                if event.button.id == "create-zone":
                        self.create_zone()
                elif event.button.id == "cancel-zone":
                        self.dismiss(None)

        def create_zone(self) -> None:
                name = self.query_one("#zone-name", Input).value.strip()
                nameserver = self.query_one(
                        "#zone-nameserver",
                        Input,
                ).value.strip()
                admin_email = self.query_one(
                        "#zone-admin-email",
                        Input,
                ).value.strip()

                if not name or not nameserver or not admin_email:
                        self._show_status(
                                "All fields are required."
                        )
                        return

                normalized_name = name.rstrip(".").lower()

                if (
                        not normalized_name
                        or any(
                                not label
                                for label in normalized_name.split(".")
                        )
                ):
                        self._show_status(
                                "Enter a valid dotted zone name."
                        )
                        return

                zone = Zone(
                        name=normalized_name,
                        nameserver=nameserver,
                        admin_email=admin_email,
                        zone_type=ZoneType.PRIMARY,
                )

                self.dismiss(zone)

        def _show_status(self, message: str) -> None:
                self.query_one(
                        "#add-zone-status",
                        Static,
                ).update(message)
