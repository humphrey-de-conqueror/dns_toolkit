
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static


class ConfirmScreen(Screen):
        def __init__(self, message: str) -> None:
                super().__init__()
                self.message = message

        def compose(self) -> ComposeResult:
                with Vertical(id="confirm-page"):
                        yield Static(
                                "Confirm Action",
                                classes="page-title",
                        )
                        yield Static(
                                self.message,
                                id="confirm-message",
                        )

                        with Horizontal():
                                yield Button(
                                        "Confirm",
                                        id="confirm-yes",
                                        variant="error",
                                )
                                yield Button(
                                        "Cancel",
                                        id="confirm-no",
                                )

        def on_button_pressed(
                self,
                event: Button.Pressed,
        ) -> None:
                if event.button.id == "confirm-yes":
                        self.dismiss(True)
                elif event.button.id == "confirm-no":
                        self.dismiss(False)
