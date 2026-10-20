
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from dns_toolkit.bind_config import render_zone_file
from dns_toolkit.models import Zone


class BindPreviewScreen(Screen):
        def __init__(self, zone: Zone) -> None:
                super().__init__()
                self.zone = zone

        def compose(self) -> ComposeResult:
                normalized_name = self.zone.name.rstrip(".").lower()

                declaration = (
                        f'zone "{normalized_name}" {{\n'
                        "        type master;\n"
                        f'        file "zones/db.{normalized_name}";\n'
                        "};"
                )

                try:
                        zone_content = render_zone_file(
                                self.zone,
                                serial=1,
                        )
                        preview = (
                                "BIND zone declaration\n"
                                "=====================\n"
                                f"{declaration}\n\n"
                                "Zone file\n"
                                "=========\n"
                                f"{zone_content}"
                        )
                except (ValueError, OSError) as error:
                        preview = (
                                "Could not generate the preview:\n"
                                f"{error}"
                        )

                with Vertical(id="bind-preview-page"):
                        yield Static(
                                f"BIND Preview: {normalized_name}",
                                classes="page-title",
                        )
                        yield Static(
                                preview,
                                id="bind-preview-content",
                                markup=False,
                        )
                        yield Button("Close", id="close-preview")

        def on_button_pressed(
                self,
                event: Button.Pressed,
        ) -> None:
                if event.button.id == "close-preview":
                        self.dismiss()
