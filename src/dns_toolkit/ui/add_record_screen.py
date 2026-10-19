
import ipaddress
import re

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

from dns_toolkit.models import DNSRecord, Zone


DOMAIN_PATTERN = re.compile(
        r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*\.?$"
)

OWNER_PATTERN = re.compile(
        r"^(?:@|[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*)$"
)


class AddRecordScreen(ModalScreen[DNSRecord | None]):
        CSS = """
        AddRecordScreen {
                align: center middle;
        }

        #dialog {
                width: 72;
                height: auto;
                max-height: 90%;
                border: round $primary;
                background: $surface;
                padding: 1 2;
                overflow-y: auto;
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


        def __init__(
                self,
                zone: Zone,
                record: DNSRecord | None = None,
        ) -> None:
                super().__init__()
                self.zone = zone
                self.record = record
                self.is_editing = record is not None


        def compose(self) -> ComposeResult:
                with Vertical(id="dialog"):
                        yield Static(
                                (
                                        f"Edit Record — {self.zone.name}"
                                        if self.is_editing
                                        else f"Add Record — {self.zone.name}"
                                ),
                                id="dialog-title",
                        )

                        yield Label("Record name", classes="field-label")
                        yield Input(
                                value=self.record.name if self.record else "",
                                placeholder="@ or www",
                                id="record-name",
                        )

                        yield Label("Record type", classes="field-label")
                        yield Select(
                                [
                                        ("A — IPv4 address", "A"),
                                        ("AAAA — IPv6 address", "AAAA"),
                                        ("CNAME — Alias", "CNAME"),
                                        ("MX — Mail server", "MX"),
                                        ("NS — Nameserver", "NS"),
                                        ("TXT — Text value", "TXT"),
                                ],
                                value=(
                                        self.record.record_type
                                        if self.record
                                        else "A"
                                ),
                                id="record-type",
                        )

                        yield Label("Record value", classes="field-label")
                        yield Input(
                                value=self.record.value if self.record else "",
                                placeholder="192.0.2.10",
                                id="record-value",
                        )

                        yield Label("TTL in seconds", classes="field-label")
                        yield Input(
                                value=str(self.record.ttl) if self.record else "3600",
                                placeholder="3600",
                                id="record-ttl",
                        )

                        yield Static("", id="form-error")

                        with Horizontal(id="form-actions"):
                                yield Button("Cancel", id="cancel")
                                yield Button(
                                        "Save Changes" if self.is_editing else "Add Record",
                                        variant="primary",
                                        id="create-record",
                                )

        def on_mount(self) -> None:
                self.query_one("#record-name", Input).focus()

        def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "cancel":
                        self.dismiss(None)
                elif event.button.id == "create-record":
                        self._create_record()

        def _create_record(self) -> None:
                name = self.query_one("#record-name", Input).value.strip()
                record_type = self.query_one("#record-type", Select).value
                value = self.query_one("#record-value", Input).value.strip()
                ttl_text = self.query_one("#record-ttl", Input).value.strip()

                error = self.query_one("#form-error", Static)

                if not name or not value or not ttl_text:
                        error.update("All fields are required.")
                        return

                if not OWNER_PATTERN.fullmatch(name):
                        error.update(
                                "Use @ or a relative hostname, such as www "
                                "or api.www. Do not enter a full domain name."
                        )
                        return

                try:
                        ttl = int(ttl_text)
                except ValueError:
                        error.update("TTL must be a positive integer.")
                        return

                if not 1 <= ttl <= 2147483647:
                        error.update("TTL must be between 1 and 2147483647.")
                        return

                if not isinstance(record_type, str):
                        error.update("Select a record type.")
                        return

                value = self._normalize_value(record_type, value, error)

                if value is None:
                        return

                self.dismiss(
                        DNSRecord(
                                name=name.lower(),
                                record_type=record_type,
                                value=value,
                                ttl=ttl,
                        )
                )

        def _normalize_value(
                self,
                record_type: str,
                value: str,
                error: Static,
        ) -> str | None:
                if record_type == "A":
                        try:
                                address = ipaddress.ip_address(value)
                        except ValueError:
                                error.update("Enter a valid IPv4 address.")
                                return None

                        if address.version != 4:
                                error.update("An A record requires an IPv4 address.")
                                return None

                        return str(address)

                if record_type == "AAAA":
                        try:
                                address = ipaddress.ip_address(value)
                        except ValueError:
                                error.update("Enter a valid IPv6 address.")
                                return None

                        if address.version != 6:
                                error.update("An AAAA record requires an IPv6 address.")
                                return None

                        return str(address)

                if record_type in {"CNAME", "NS"}:
                        target = value.rstrip(".")

                        if not DOMAIN_PATTERN.fullmatch(target):
                                error.update(
                                        "Enter a valid target domain name."
                                )
                                return None

                        return target.lower() + "."

                if record_type == "MX":
                        parts = value.split()

                        if len(parts) != 2 or not parts[0].isdigit():
                                error.update(
                                        "Enter MX as: priority mail.example.test"
                                )
                                return None

                        priority = int(parts[0])
                        target = parts[1].rstrip(".")

                        if not 0 <= priority <= 65535:
                                error.update(
                                        "MX priority must be between 0 and 65535."
                                )
                                return None

                        if not DOMAIN_PATTERN.fullmatch(target):
                                error.update(
                                        "Enter a valid mail server domain name."
                                )
                                return None

                        return f"{priority} {target.lower()}."

                if record_type == "TXT":
                        if len(value.encode("utf-8")) > 255:
                                error.update(
                                        "TXT input is limited to 255 UTF-8 bytes "
                                        "for this initial form."
                                )
                                return None

                        return value

                error.update("Unsupported record type.")
                return None

        def action_cancel(self) -> None:
                self.dismiss(None)
