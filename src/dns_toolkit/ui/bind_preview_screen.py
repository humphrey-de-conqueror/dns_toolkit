
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static, TextArea

from dns_toolkit.bind_config import render_zone_preview
from dns_toolkit.models import Zone


class BindPreviewScreen(ModalScreen[None]):
        CSS = """
        BindPreviewScreen {
                align: center middle;
        }

        #dialog {
                width: 95%;
                height: 90%;
                border: round $primary;
                background: $surface;
                padding: 1 2;
        }

        #preview-title {
                height: auto;
                text-style: bold;
                color: $accent;
                margin-bottom: 1;
        }

        #preview-content {
                height: 1fr;
                margin-bottom: 1;
        }

        #preview-actions {
                height: 3;
                align-horizontal: right;
        }

        #preview-actions Button {
                width: auto;
                margin-left: 1;
        }
        """

        BINDINGS = [
                ("escape", "close_preview", "Close"),
        ]

        def __init__(self, zone: Zone) -> None:
                super().__init__()
                self.zone = zone


        def compose(self) -> ComposeResult:
                try:
                        preview = render_zone_preview(self.zone)
                except ValueError as error:
                        preview = (
                                "Configuration validation failed.\n\n"
                                f"{error}\n\n"
                                "Correct the zone or record data, then try again."
                        )

                with Vertical(id="dialog"):
                        yield Static(
                                f"BIND Configuration Preview — {self.zone.name}",
                                id="preview-title",
                        )

                        yield TextArea(
                                preview,
                                read_only=True,
                                id="preview-content",
                        )

                        with Horizontal(id="preview-actions"):
                                yield Button(
                                        "Close",
                                        id="close",
                                )


        def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "close":
                        self.dismiss(None)

        def action_close_preview(self) -> None:
                self.dismiss(None)
