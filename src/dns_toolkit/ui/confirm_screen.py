
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmScreen(ModalScreen[bool]):
        CSS = """
        ConfirmScreen {
                align: center middle;
        }

        #dialog {
                width: 64;
                height: auto;
                max-height: 80%;
                border: round $error;
                background: $surface;
                padding: 1 2;
        }

        #message {
                height: auto;
                margin-bottom: 2;
        }

        #actions {
                height: auto;
                align-horizontal: right;
        }

        #actions Button {
                margin-left: 1;
        }
        """

        BINDINGS = [
                ("escape", "cancel", "Cancel"),
        ]

        def __init__(
                self,
                title: str,
                message: str,
                confirm_label: str = "Delete",
        ) -> None:
                super().__init__()
                self.dialog_title = title
                self.message = message
                self.confirm_label = confirm_label

        def compose(self) -> ComposeResult:
                with Vertical(id="dialog"):
                        yield Static(
                                self.dialog_title,
                                classes="section-title",
                        )
                        yield Static(self.message, id="message")

                        with Horizontal(id="actions"):
                                yield Button("Cancel", id="cancel")
                                yield Button(
                                        self.confirm_label,
                                        variant="error",
                                        id="confirm",
                                )

        def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "confirm":
                        self.dismiss(True)
                elif event.button.id == "cancel":
                        self.dismiss(False)

        def action_cancel(self) -> None:
                self.dismiss(False)
