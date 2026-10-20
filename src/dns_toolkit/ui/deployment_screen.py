
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from dns_toolkit.ui.navigation_screen import NavigationScreen
from textual.widgets import Button, Checkbox, Static

from dns_toolkit.repositories import ZoneRepository
from dns_toolkit.services.deployment_service import DeploymentService
from dns_toolkit.storage.settings_repository import SettingsRepository


class DeploymentScreen(NavigationScreen):
        def __init__(
                self,
                deployment_service: DeploymentService,
                zone_repository: ZoneRepository,
                settings_repository: SettingsRepository,
        ) -> None:
                super().__init__()

                self.deployment_service = deployment_service
                self.zone_repository = zone_repository
                self.settings_repository = settings_repository
                self.plan = None

        def compose_page(self) -> ComposeResult:
                with Vertical(id="deployment-page"):
                        yield Static(
                                "Deployment",
                                classes="page-title",
                        )
                        yield Static(
                                "Prepare and validate a candidate BIND "
                                "configuration before deployment."
                        )
                        yield Static(
                                "No live system files are changed during "
                                "preparation or validation."
                        )

                        with Horizontal():
                                yield Button(
                                        "Prepare Plan",
                                        id="prepare-deployment",
                                        variant="primary",
                                )
                                yield Button(
                                        "Validate Plan",
                                        id="validate-deployment",
                                )

                        yield Static(
                                "No deployment plan prepared.",
                                id="deployment-files",
                        )
                        yield Static(
                                "Validation has not run.",
                                id="deployment-validation",
                        )

                        yield Checkbox(
                                "I have reviewed the plan and confirm "
                                "the deployment request.",
                                id="deployment-confirm",
                        )

                        with Horizontal():
                                yield Button(
                                        "Request Deployment",
                                        id="execute-deployment",
                                        variant="error",
                                )
                                yield Button(
                                        "Back",
                                        id="back-deployment",
                                )

                        yield Static(
                                "Live deployment is disabled until the "
                                "privileged helper and rollback workflow "
                                "are implemented.",
                                id="deployment-status",
                        )

                        yield Static(
                                "Privileged helper status has not been checked.",
                                id="deployment-helper-status",
                        )
                        yield Button(
                                "Check Helper",
                                id="check-deployment-helper",
                        )


        def on_mount(self) -> None:
                settings = self.settings_repository.load()

                self.query_one("#deployment-files", Static).update(
                        "BIND configuration: "
                        f"{settings.bind_config_path}\n"
                        "Zone directory: "
                        f"{settings.zone_file_directory}"
                )

        def on_button_pressed(self, event: Button.Pressed) -> None:
                actions = {
                        "prepare-deployment": self.prepare_plan,
                        "validate-deployment": self.validate_plan,
                        "execute-deployment": self.request_deployment,
                        "check-deployment-helper": self.check_helper,
                        "back-deployment": self.dismiss,
                }

                action = actions.get(event.button.id)

                if action is not None:
                        action()

        def prepare_plan(self) -> None:
                settings = self.settings_repository.load()
                zones = self.zone_repository.list_zones()

                zone_directory = Path(
                        settings.zone_file_directory
                ).expanduser()

                try:
                        self.plan = self.deployment_service.prepare(
                                zones=zones,
                                zone_directory=zone_directory,
                        )
                except (OSError, ValueError) as error:
                        self.plan = None
                        self.query_one(
                                "#deployment-status",
                                Static,
                        ).update(
                                f"Could not prepare deployment plan: {error}"
                        )
                        return

                file_lines = [
                        f"Target: {self.plan.target_name}",
                        f"Files planned: {self.plan.file_count}",
                        "",
                ]

                file_lines.extend(
                        str(path)
                        for path in self.plan.files
                )

                if self.plan.validation_errors:
                        file_lines.extend(
                                [
                                        "",
                                        "Application validation errors:",
                                ]
                        )
                        file_lines.extend(
                                f"- {error}"
                                for error in self.plan.validation_errors
                        )

                self.query_one(
                        "#deployment-files",
                        Static,
                ).update("\n".join(file_lines))

                self.query_one(
                        "#deployment-validation",
                        Static,
                ).update(
                        "Plan prepared. Run Validate Plan before "
                        "requesting deployment."
                )

                self.query_one(
                        "#deployment-confirm",
                        Checkbox,
                ).value = False

                self.query_one(
                        "#deployment-status",
                        Static,
                ).update(
                        "Plan prepared. No system files have been changed."
                )

        def validate_plan(self) -> None:
                if self.plan is None:
                        self.query_one(
                                "#deployment-validation",
                                Static,
                        ).update(
                                "Prepare a deployment plan first."
                        )
                        return

                valid, message = (
                        self.deployment_service.validate_plan(self.plan)
                )

                status = (
                        "Candidate validation passed."
                        if valid
                        else "Candidate validation failed."
                )

                self.query_one(
                        "#deployment-validation",
                        Static,
                ).update(f"{status}\n{message}")

                self.query_one(
                        "#deployment-confirm",
                        Checkbox,
                ).value = False

                self.query_one(
                        "#deployment-status",
                        Static,
                ).update(
                        "Validation completed. This does not install "
                        "or activate the candidate configuration."
                )

        def request_deployment(self) -> None:
                if self.plan is None:
                        self.query_one(
                                "#deployment-status",
                                Static,
                        ).update(
                                "Prepare a deployment plan first."
                        )
                        return

                confirmed = self.query_one(
                        "#deployment-confirm",
                        Checkbox,
                ).value

                if not confirmed:
                        self.query_one(
                                "#deployment-status",
                                Static,
                        ).update(
                                "Check the confirmation box before "
                                "requesting deployment."
                        )
                        return

                result = self.deployment_service.deploy(
                        plan=self.plan,
                        confirmed=True,
                )

                self.query_one(
                        "#deployment-status",
                        Static,
                ).update(
                        f"{result.message}\n"
                        f"Success: {result.success}"
                )

        def check_helper(self) -> None:
                ready, message = self.deployment_service.preflight()

                self.query_one(
                        "#deployment-helper-status",
                        Static,
                ).update(
                        f"Helper preflight: {'passed' if ready else 'blocked'}\n"
                        f"{message}"
                )

