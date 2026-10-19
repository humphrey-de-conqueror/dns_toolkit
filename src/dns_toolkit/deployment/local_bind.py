
import shutil
import subprocess
import tempfile
from pathlib import Path

from dns_toolkit.deployment.base import (
        DeploymentBackend,
        DeploymentResult,
)
from dns_toolkit.deployment.plan import DeploymentPlan


class LocalBindBackend(DeploymentBackend):
        def __init__(
                self,
                config_path: Path = Path("/etc/bind/named.conf"),
                service_name: str = "bind9",
        ) -> None:
                self.config_path = config_path
                self.service_name = service_name

        def inspect(self) -> dict[str, object]:
                return {
                        "platform": "local-linux",
                        "config_path": str(self.config_path),
                        "bind_available": shutil.which("named") is not None,
                        "checkconf_available": (
                                shutil.which("named-checkconf") is not None
                        ),
                        "checkzone_available": (
                                shutil.which("named-checkzone") is not None
                        ),
                        "systemctl_available": (
                                shutil.which("systemctl") is not None
                        ),
                }

        def validate(
                self,
                config_path: Path,
        ) -> tuple[bool, str]:
                checker = shutil.which("named-checkconf")

                if checker is None:
                        return False, "named-checkconf is not installed."

                if not config_path.is_file():
                        return False, f"Configuration not found: {config_path}"

                result = subprocess.run(
                        [checker, str(config_path)],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=30,
                )

                output = "\n".join(
                        part
                        for part in (result.stdout, result.stderr)
                        if part
                )

                return (
                        result.returncode == 0,
                        output or "Configuration validation passed.",
                )

        def validate_plan(
                self,
                plan: DeploymentPlan,
        ) -> tuple[bool, str]:
                if plan.validation_errors:
                        return False, "\n".join(plan.validation_errors)

                checkzone = shutil.which("named-checkzone")
                checkconf = shutil.which("named-checkconf")

                if checkzone is None or checkconf is None:
                        return (
                                False,
                                "Install BIND utilities named-checkzone "
                                "and named-checkconf before validating "
                                "a deployment plan.",
                        )

                output_lines: list[str] = []

                with tempfile.TemporaryDirectory(
                        prefix="dns-toolkit-validation-"
                ) as temporary_directory:
                        temporary_root = Path(temporary_directory)
                        temporary_zone_directory = (
                                temporary_root / "zones"
                        )
                        temporary_zone_directory.mkdir()

                        declarations: list[str] = []

                        for destination, content in plan.files.items():
                                if not destination.name.startswith("db."):
                                        continue

                                zone_name = destination.name[3:]
                                temporary_zone_path = (
                                        temporary_zone_directory
                                        / destination.name
                                )
                                temporary_zone_path.write_text(
                                        content,
                                        encoding="utf-8",
                                )

                                result = subprocess.run(
                                        [
                                                checkzone,
                                                zone_name,
                                                str(temporary_zone_path),
                                        ],
                                        capture_output=True,
                                        text=True,
                                        check=False,
                                        timeout=30,
                                )

                                output = "\n".join(
                                        part
                                        for part in (
                                                result.stdout,
                                                result.stderr,
                                        )
                                        if part
                                )
                                output_lines.append(
                                        output
                                        or f"Validated zone {zone_name}."
                                )

                                if result.returncode != 0:
                                        return False, "\n".join(
                                                output_lines
                                        )

                                declarations.append(
                                        f'zone "{zone_name}" {{\n'
                                        "        type master;\n"
                                        f'        file "{temporary_zone_path}";\n'
                                        "};\n"
                                )

                        candidate_config = (
                                temporary_root / "named.conf"
                        )
                        candidate_config.write_text(
                                'options { directory "'
                                + str(temporary_root).replace('"', '\\"')
                                + '"; };\n\n'
                                + "\n".join(declarations),
                                encoding="utf-8",
                        )

                        result = subprocess.run(
                                [checkconf, str(candidate_config)],
                                capture_output=True,
                                text=True,
                                check=False,
                                timeout=30,
                        )

                        output = "\n".join(
                                part
                                for part in (
                                        result.stdout,
                                        result.stderr,
                                )
                                if part
                        )

                        output_lines.append(
                                output
                                or "Candidate configuration syntax is valid."
                        )

                        if result.returncode != 0:
                                return False, "\n".join(output_lines)

                return True, "\n".join(output_lines)

        def deploy(
                self,
                config_path: Path,
                zone_files: dict[Path, str],
                confirmed: bool,
        ) -> DeploymentResult:
                if not confirmed:
                        return DeploymentResult(
                                success=False,
                                message="Deployment was not confirmed.",
                                changed_files=[],
                        )

                return DeploymentResult(
                        success=False,
                        message=(
                                "Live deployment remains disabled. "
                                "The privileged helper and transactional "
                                "activation workflow are not installed."
                        ),
                        changed_files=[],
                )
