
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

from dns_toolkit.deployment.local_bind import LocalBindBackend
from dns_toolkit.repositories import ZoneRepository
from dns_toolkit.services.bind_service import BindService
from dns_toolkit.services.deployment_service import DeploymentService
from dns_toolkit.services.diagnostics_service import DiagnosticsService
from dns_toolkit.services.export_service import ExportService
from dns_toolkit.services.target_service import TargetService
from dns_toolkit.storage.settings_repository import SettingsRepository
from dns_toolkit.ui.dashboard_screen import DashboardScreen
from dns_toolkit.ui.deployment_screen import DeploymentScreen
from dns_toolkit.ui.diagnostics_screen import DiagnosticsScreen
from dns_toolkit.ui.records_screen import RecordsScreen
from dns_toolkit.ui.settings_screen import SettingsScreen
from dns_toolkit.ui.target_screen import TargetScreen
from dns_toolkit.ui.zones_screen import ZonesScreen
from dns_toolkit.ui.export_screen import ExportScreen


class DNSToolkitApp(App[None]):
        TITLE = "DNS Toolkit"
        SUB_TITLE = "BIND 9 Management Console"
        CSS_PATH = "app.tcss"

        def __init__(self) -> None:
                super().__init__()

                self.settings_repository = SettingsRepository()
                self.settings = self.settings_repository.load()

                self.zone_repository = ZoneRepository()
                self.bind_service = BindService(
                        service_name=self.settings.bind_service_name,
                )
                self.target_service = TargetService()

                available_targets = {
                        target.target_id
                        for target in self.target_service.list_targets()
                }

                if self.settings.active_target_id in available_targets:
                        self.target_service.select_target(
                                self.settings.active_target_id
                        )

                backend = LocalBindBackend(
                        config_path=Path(
                                self.settings.bind_config_path
                        ).expanduser(),
                        service_name=self.settings.bind_service_name,
                )

                self.deployment_service = DeploymentService(backend)
                self.diagnostics_service = DiagnosticsService(
                        bind_service=self.bind_service,
                        backend=backend,
                )
                self.export_service = ExportService()

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
                                yield Button(
                                        "Targets",
                                        id="nav-targets",
                                )
                                yield Button(
                                        "Diagnostics",
                                        id="nav-diagnostics",
                                )
                                yield Button(
                                        "Export",
                                        id="nav-export"
                                )
                                yield Button(
                                        "Settings",
                                        id="nav-settings",
                                )
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
                        "nav-export": self.show_export,
                        "nav-settings": self.show_settings,
                        "refresh-dashboard": self.refresh_dashboard,
                }

                action = actions.get(event.button.id)

                if action is not None:
                        action()

        def refresh_dashboard(self) -> None:
                target = self.target_service.get_active_target()
                service = self.bind_service.get_service_status()
                executables = self.bind_service.get_executables()
                zones = self.zone_repository.list_zones()

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
                while self.screen_stack and len(self.screen_stack) > 1:
                        self.pop_screen()

                self.query_one("#page-heading", Static).update("Dashboard")
                self.refresh_dashboard()

        def show_zones(self) -> None:
                self.push_screen(ZonesScreen(self.zone_repository))

        def show_records(self) -> None:
                self.push_screen(RecordsScreen(self.zone_repository))

        def show_deployment(self) -> None:
                self.push_screen(
                        DeploymentScreen(
                                deployment_service=self.deployment_service,
                                zone_repository=self.zone_repository,
                                settings_repository=self.settings_repository,
                        )
                )

        def show_targets(self) -> None:
                self.push_screen(
                        TargetScreen(
                                target_service=self.target_service,
                                settings_repository=self.settings_repository,
                        )
                )

        def show_diagnostics(self) -> None:
                self.push_screen(
                        DiagnosticsScreen(self.diagnostics_service)
                )

        def show_export(self) -> None:
                self.push_screen(
                        ExportScreen(
                                export_service=self.export_service,
                                zone_repository=self.zone_repository,
                                settings_repository=self.settings_repository,
                        )
                )

        def show_settings(self) -> None:
                self.push_screen(
                        SettingsScreen(self.settings_repository)
                )


def main() -> None:
        DNSToolkitApp().run()
