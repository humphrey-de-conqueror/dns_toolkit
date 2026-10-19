
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Select, Static

from dns_toolkit.services.target_service import TargetService
from dns_toolkit.storage.settings_repository import SettingsRepository


class TargetScreen(Screen):
        def __init__(
                self,
                target_service: TargetService,
                settings_repository: SettingsRepository,
        ) -> None:
                super().__init__()
                self.target_service = target_service
                self.settings_repository = settings_repository

        def compose(self) -> ComposeResult:
                active_target = self.target_service.get_active_target()
                targets = [
                        (target.name, target.target_id)
                        for target in self.target_service.list_targets()
                        if target.enabled
                ]

                with Vertical(id="target-page"):
                        yield Static(
                                "Deployment Targets",
                                classes="page-title",
                        )
                        yield Static(
                                f"Current target: {active_target.name}",
                                id="current-target",
                        )
                        yield Select(
                                targets,
                                value=active_target.target_id,
                                id="target-select",
                        )
                        yield Button("Use Selected Target", id="select-target")
                        yield Static("", id="target-status")
                        yield Button("Back", id="back")

        def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "select-target":
                        self.select_target()
                elif event.button.id == "back":
                        self.app.pop_screen()

        def select_target(self) -> None:
                selected = self.query_one(
                        "#target-select",
                        Select,
                ).value

                if selected is Select.BLANK:
                        self.query_one("#target-status", Static).update(
                                "Select a deployment target first."
                        )
                        return

                try:
                        target = self.target_service.select_target(str(selected))
                        self.settings_repository.update(
                                active_target_id=target.target_id
                        )

                        self.query_one("#current-target", Static).update(
                                f"Current target: {target.name}"
                        )
                        message = f"Selected target: {target.name}"
                except (ValueError, NotImplementedError, OSError) as error:
                        message = f"Could not select target: {error}"

                self.query_one("#target-status", Static).update(message)
