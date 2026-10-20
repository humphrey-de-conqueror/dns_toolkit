
from pathlib import Path

from dns_toolkit.deployment.base import DeploymentResult
from dns_toolkit.deployment.helper_status import (
        DEFAULT_HELPER_PATH,
        HelperStatus,
)
from dns_toolkit.deployment.local_bind import LocalBindBackend
from dns_toolkit.deployment.manifest import DeploymentManifest
from dns_toolkit.deployment.manifest_stager import ManifestStager
from dns_toolkit.deployment.plan import DeploymentPlan
from dns_toolkit.deployment.plan_builder import DeploymentPlanBuilder
from dns_toolkit.deployment.privilege import PrivilegeManager
from dns_toolkit.models import Zone


class DeploymentService:
        def __init__(
                self,
                backend: LocalBindBackend,
                plan_builder: DeploymentPlanBuilder | None = None,
                manifest_stager: ManifestStager | None = None,
                helper_status: HelperStatus | None = None,
                live_deployment_enabled: bool = False,
        ) -> None:
                self.backend = backend
                self.plan_builder = (
                        plan_builder or DeploymentPlanBuilder()
                )
                self.manifest_stager = (
                        manifest_stager or ManifestStager()
                )
                self.helper_status = (
                        helper_status or HelperStatus()
                )
                self.live_deployment_enabled = (
                        live_deployment_enabled
                )
                self.privilege_manager = PrivilegeManager(
                        DEFAULT_HELPER_PATH
                )

        def inspect_target(self) -> dict[str, object]:
                return self.backend.inspect()

        def inspect_helper(self) -> dict[str, object]:
                return self.helper_status.inspect()

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

        def preflight(self) -> tuple[bool, str]:
                helper = self.inspect_helper()
                messages = [
                        f"Helper path: {helper['helper_path']}",
                        f"Helper exists: {helper['helper_exists']}",
                        f"Root-owned: {helper['helper_root_owned']}",
                        "Protected from group/other writes: "
                        f"{helper['helper_not_writable_by_others']}",
                        f"pkexec available: {helper['pkexec_available']}",
                ]

                ready = bool(helper["ready_for_review"])

                if not ready:
                        messages.append(
                                "Privileged helper preflight failed."
                        )

                if not self.live_deployment_enabled:
                        messages.append(
                                "Live deployment is disabled by application "
                                "configuration."
                        )
                        ready = False

                return ready, "\n".join(messages)

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

                valid, validation_message = (
                        self.validate_plan(plan)
                )

                if not valid:
                        return DeploymentResult(
                                success=False,
                                message=(
                                        "Candidate validation failed:\n"
                                        + validation_message
                                ),
                                changed_files=[],
                        )

                ready, preflight_message = self.preflight()

                if not ready:
                        return DeploymentResult(
                                success=False,
                                message=(
                                        "Deployment was not started.\n"
                                        + preflight_message
                                ),
                                changed_files=[],
                        )

                manifest = DeploymentManifest.from_plan(plan)
                manifest_path = self.manifest_stager.stage(manifest)

                try:
                        success, output = self.privilege_manager.run(
                                "install",
                                [
                                        "--manifest",
                                        str(manifest_path),
                                ],
                        )
                finally:
                        self.manifest_stager.cleanup(manifest_path)

                return DeploymentResult(
                        success=success,
                        message=(
                                "Deployment completed."
                                if success
                                else "Deployment failed."
                        ),
                        changed_files=(
                                list(plan.files)
                                if success
                                else []
                        ),
                        command_output=output,
                )
