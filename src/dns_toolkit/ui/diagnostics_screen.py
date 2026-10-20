
from textual.app import ComposeResult
from textual.containers import Vertical
from dns_toolkit.ui.navigation_screen import NavigationScreen
from textual.widgets import Button, Static

from dns_toolkit.services.diagnostics_service import DiagnosticsService


class DiagnosticsScreen(NavigationScreen):
        def __init__(
                self,
                diagnostics_service: DiagnosticsService,
        ) -> None:
                super().__init__()
                self.diagnostics_service = diagnostics_service

        def compose_page(self) -> ComposeResult:
                with Vertical(id="diagnostics"):
                        yield Static("System Diagnostics", classes="page-title")
                        yield Static("", id="diagnostics-results")
                        yield Button("Refresh Diagnostics", id="refresh")
                        yield Button("Back", id="back")

        def on_mount(self) -> None:
                self.refresh_diagnostics()

        def refresh_diagnostics(self) -> None:
                data = self.diagnostics_service.collect()
                lines = ["Environment"]

                for key, value in data["environment"].items():
                        lines.append(f"  {key}: {value}")

                lines.append("")
                lines.append("BIND Executables")

                for name, path in data["executables"].items():
                        lines.append(
                                f"  {name}: {path or 'Not found'}"
                        )

                lines.append("")
                lines.append("Service")

                for key, value in data["service"].items():
                        lines.append(f"  {key}: {value}")

                self.query_one("#diagnostics-results", Static).update(
                        "\n".join(lines)
                )

        def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "refresh":
                        self.refresh_diagnostics()
                elif event.button.id == "back":
                        self.app.pop_screen()
