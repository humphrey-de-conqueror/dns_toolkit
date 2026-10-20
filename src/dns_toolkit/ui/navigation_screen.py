from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static


class NavigationScreen(Screen):
        def compose(self) -> ComposeResult:
                with Horizontal(id="app-layout"):
                        with Vertical(id="sidebar"):
                                yield Static("DNS TOOLKIT", id="brand")
                                yield Button("Dashboard", id="nav-dashboard")
                                yield Button("Zones", id="nav-zones")
                                yield Button("Records", id="nav-records")
                                yield Button(
                                        "Deployment",
                                        id="nav-deployment",
                                )
                                yield Button("Targets", id="nav-targets")
                                yield Button(
                                        "Diagnostics",
                                        id="nav-diagnostics",
                                )
                                yield Button("Settings", id="nav-settings")
                                yield Button("Export", id="nav-export")
                                yield Static(
                                        "BIND 9 · Local Linux",
                                        id="sidebar-footer",
                                )

                        with Vertical(id="main-content"):
                                yield from self.compose_page()

        def compose_page(self) -> ComposeResult:
                yield Static("Page content has not been implemented.")

        @on(Button.Pressed, "#nav-dashboard")
        def navigate_dashboard(self) -> None:
                self.app.show_dashboard()

        @on(Button.Pressed, "#nav-zones")
        def navigate_zones(self) -> None:
                self.app.show_zones()

        @on(Button.Pressed, "#nav-records")
        def navigate_records(self) -> None:
                self.app.show_records()

        @on(Button.Pressed, "#nav-deployment")
        def navigate_deployment(self) -> None:
                self.app.show_deployment()

        @on(Button.Pressed, "#nav-targets")
        def navigate_targets(self) -> None:
                self.app.show_targets()

        @on(Button.Pressed, "#nav-diagnostics")
        def navigate_diagnostics(self) -> None:
                self.app.show_diagnostics()

        @on(Button.Pressed, "#nav-settings")
        def navigate_settings(self) -> None:
                self.app.show_settings()

        @on(Button.Pressed, "#nav-export")
        def navigate_export(self) -> None:
                self.app.show_export()