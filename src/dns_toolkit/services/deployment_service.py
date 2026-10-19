
from pathlib import Path

from dns_toolkit.deployment.base import DeploymentResult
from dns_toolkit.deployment.local_bind import LocalBindBackend
from dns_toolkit.deployment.plan import DeploymentPlan
from dns_toolkit.deployment.plan_builder import DeploymentPlanBuilder
from dns_toolkit.models import Zone


class DeploymentService:
        def __init__(
                self,
                backend: LocalBindBackend,
                plan_builder: DeploymentPlanBuilder | None = None,
        ) -> None:
                self.backend = backend
                self.plan_builder = (
                        plan_builder or DeploymentPlanBuilder()
                )

        def inspect_target(self) -> dict[str, object]:
                return self.backend.inspect()

        def validate(
                self,
                config_path: Path,
        ) -> tuple[bool, str]:
                return self.backend.validate(config_path)

        def prepare(
                self,
                zones: list[Zone],
                zone_directory: Path,
                target_name: str = "Local BIND 9",
        ) -> DeploymentPlan:
                return self.plan_builder.build(
                        zones=zones,
                        config_path=self.backend.config_path,
                        zone_directory=zone_directory,
                        target_name=target_name,
                )

        def validate_plan(
                self,
                plan: DeploymentPlan,
        ) -> tuple[bool, str]:
                return self.backend.validate_plan(plan)

        def deploy(
                self,
                plan: DeploymentPlan,
                confirmed: bool,
        ) -> DeploymentResult:
                if not confirmed:
                        return DeploymentResult(
                                success=False,
                                message="Deployment was not confirmed.",
                                changed_files=[],
                        )

                if not plan.is_valid:
                        return DeploymentResult(
                                success=False,
                                message=(
                                        "Deployment plan has validation "
                                        "errors:\n"
                                        + "\n".join(
                                                plan.validation_errors
                                        )
                                ),
                                changed_files=[],
                        )

                valid, message = self.validate_plan(plan)

                if not valid:
                        return DeploymentResult(
                                success=False,
                                message=(
                                        "Candidate validation failed:\n"
                                        + message
                                ),
                                changed_files=[],
                        )

                return self.backend.deploy(
                        config_path=plan.config_path,
                        zone_files=plan.files,
                        confirmed=confirmed,
                )
