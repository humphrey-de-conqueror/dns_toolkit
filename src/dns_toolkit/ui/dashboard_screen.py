
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static

from dns_toolkit.services.bind_service import BindService
from dns_toolkit.services.target_service import TargetService


class DashboardScreen(Screen):
        def __init__(
                self,
                bind_service: BindService,
                target_service: TargetService,
                zone_repository,
        ) -> None:
                super().__init__()
                self.bind_service = bind_service
                self.target_service = target_service
                self.zone_repository = zone_repository

        def compose(self) -> ComposeResult:
                with Vertical(id="dashboard"):
                        yield Static("DNS Toolkit", classes="page-title")
                        yield Static("", id="dashboard-target")
                        yield Static("", id="dashboard-service")
                        yield Static("", id="dashboard-zones")
                        yield Static("", id="dashboard-tools")

        def on_mount(self) -> None:
                self.refresh_dashboard()

        def refresh_dashboard(self) -> None:
                target = self.target_service.get_active_target()
                service = self.bind_service.get_service_status()
                executables = self.bind_service.get_executables()
                zones = self.zone_repository.list_zones()

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

                available = sum(
                        path is not None
                        for path in executables.values()
                )

                self.query_one("#dashboard-tools", Static).update(
                        f"BIND tools available: {available}/"
                        f"{len(executables)}"
                )
