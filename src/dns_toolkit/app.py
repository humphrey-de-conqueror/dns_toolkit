from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

from dns_toolkit.services.application_services import ApplicationServices
from dns_toolkit.ui.deployment_screen import DeploymentScreen
from dns_toolkit.ui.diagnostics_screen import DiagnosticsScreen
from dns_toolkit.ui.export_screen import ExportScreen
from dns_toolkit.ui.records_screen import RecordsScreen
from dns_toolkit.ui.settings_screen import SettingsScreen
from dns_toolkit.ui.target_screen import TargetScreen
from dns_toolkit.ui.zones_screen import ZonesScreen
from textual.screen import Screen


class DNSToolkitApp(App[None]):
        TITLE = "DNS Toolkit"
        SUB_TITLE = "BIND 9 Management Console"
        CSS_PATH = "app.tcss"

        def __init__(self) -> None:
                super().__init__()
                self.services = ApplicationServices()

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
                                yield Static(
                                        "Dashboard",
                                        id="page-heading",
                                )
                                yield Static(
                                        "DNS Toolkit is ready.",
                                        id="dashboard-message",
                                )
                                yield Static("", id="dashboard-target")
                                yield Static("", id="dashboard-service")
                                yield Static("", id="dashboard-zones")
                                yield Static("", id="dashboard-tools")
                                yield Button(
                                        "Refresh Dashboard",
                                        id="refresh-dashboard",
                                )

        def on_mount(self) -> None:
                self.refresh_dashboard()

        def on_button_pressed(self, event: Button.Pressed) -> None:
                actions = {
                        "nav-dashboard": self.show_dashboard,
                        "nav-zones": self.show_zones,
                        "nav-records": self.show_records,
                        "nav-deployment": self.show_deployment,
                        "nav-targets": self.show_targets,
                        "nav-diagnostics": self.show_diagnostics,
                        "nav-settings": self.show_settings,
                        "nav-export": self.show_export,
                        "refresh-dashboard": self.refresh_dashboard,
                }

                action = actions.get(event.button.id)

                if action is not None:
                        action()

        def refresh_dashboard(self) -> None:

                target = self.services.target_service.get_active_target()
                service = self.services.bind_service.get_service_status()
                executables = self.services.bind_service.get_executables()
                zones = self.services.zone_repository.list_zones()

                available_tools = sum(
                        executable is not None
                        for executable in executables.values()
                )

                self.query_one("#dashboard-target", Static).update(
                        f"Deployment target: {target.name}"
                )
                self.query_one("#dashboard-service", Static).update(
                        "BIND service: "
                        f"{service.get('state', 'unknown')} "
                        f"({service.get('substate', 'unknown')})"
                )
                self.query_one("#dashboard-zones", Static).update(
                        f"Saved zones: {len(zones)}"
                )
                self.query_one("#dashboard-tools", Static).update(
                        f"Available BIND tools: {available_tools}/"
                        f"{len(executables)}"
                )
                self.query_one("#dashboard-message", Static).update(
                        service.get("message", "Dashboard refreshed.")
                )

        def show_dashboard(self) -> None:
                while len(self.screen_stack) > 1:
                        self.pop_screen()

                self.query_one("#page-heading", Static).update("Dashboard")
                self.refresh_dashboard()

        def show_zones(self) -> None:
                self.display_screen(
                        ZonesScreen(self.services.zone_repository)
                )

        def show_records(self) -> None:
                self.display_screen(
                        RecordsScreen(self.services.zone_repository)
                )

        def show_deployment(self) -> None:
                self.display_screen(
                        DeploymentScreen(
                                deployment_service=(
                                        self.services.deployment_service
                                ),
                                zone_repository=(
                                        self.services.zone_repository
                                ),
                                settings_repository=(
                                        self.services.settings_repository
                                ),
                        )
                )

        def show_targets(self) -> None:
                self.display_screen(
                        TargetScreen(
                                target_service=self.services.target_service,
                                settings_repository=(
                                        self.services.settings_repository
                                ),
                                on_saved=self.on_settings_saved,
                        )
                )

        def show_diagnostics(self) -> None:
                self.display_screen(
                        DiagnosticsScreen(
                                self.services.diagnostics_service
                        )
                )

        def show_settings(self) -> None:
                self.display_screen(
                        SettingsScreen(
                                settings_repository=(
                                        self.services.settings_repository
                                ),
                                on_saved=self.on_settings_saved,
                        )
                )

        def show_export(self) -> None:
                self.display_screen(
                        ExportScreen(
                                export_service=self.services.export_service,
                                zone_repository=(
                                        self.services.zone_repository
                                ),
                                settings_repository=(
                                        self.services.settings_repository
                                ),
                        )
                )

        def on_settings_saved(self) -> None:
                self.services.refresh_settings()

        def display_screen(self, screen: Screen) -> None:
                if len(self.screen_stack) > 1:
                        self.switch_screen(screen)
                else:
                        self.push_screen(screen)


def main() -> None:
        DNSToolkitApp().run()