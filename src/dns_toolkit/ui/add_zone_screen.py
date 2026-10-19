
import re

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from dns_toolkit.models import Zone


DOMAIN_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*\.?$"
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AddZoneScreen(ModalScreen[Zone | None]):
    CSS = """
    AddZoneScreen {
        align: center middle;
    }

    #dialog {
        width: 70;
        height: auto;
        max-height: 90%;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }

    #dialog-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .field-label {
        margin-top: 1;
        margin-bottom: 1;
    }

    #form-error {
        color: $error;
        height: auto;
        margin-top: 1;
    }

    #form-actions {
        height: auto;
        margin-top: 1;
        align-horizontal: right;
    }

    #form-actions Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Add DNS Zone", id="dialog-title")

            yield Label("Zone name", classes="field-label")
            yield Input(
                placeholder="lab.example.test",
                id="zone-name",
            )

            yield Label("Authoritative nameserver", classes="field-label")
            yield Input(
                placeholder="ns1.lab.example.test",
                id="nameserver",
            )

            yield Label("Administrator email", classes="field-label")
            yield Input(
                placeholder="admin@example.test",
                id="admin-email",
            )

            yield Static("", id="form-error")

            with Horizontal(id="form-actions"):
                yield Button("Cancel", id="cancel")
                yield Button(
                    "Create Zone",
                    variant="primary",
                    id="create-zone",
                )

    def on_mount(self) -> None:
        self.query_one("#zone-name", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "create-zone":
            self._create_zone()

    def _create_zone(self) -> None:
        name = self.query_one("#zone-name", Input).value.strip().rstrip(".").lower()
        nameserver = (
            self.query_one("#nameserver", Input)
            .value.strip()
            .rstrip(".")
            .lower()
        )
        email = self.query_one("#admin-email", Input).value.strip()

        error = self.query_one("#form-error", Static)

        if not name or not nameserver or not email:
            error.update("All fields are required.")
            return

        if not DOMAIN_PATTERN.fullmatch(name):
            error.update("Enter a valid DNS zone name.")
            return

        if not DOMAIN_PATTERN.fullmatch(nameserver):
            error.update("Enter a valid nameserver domain name.")
            return

        if not EMAIL_PATTERN.fullmatch(email):
            error.update("Enter a valid administrator email address.")
            return

        zone = Zone(
            name=name,
            nameserver=nameserver,
            admin_email=email,
        )
        self.dismiss(zone)

    def action_cancel(self) -> None:
        self.dismiss(None)
