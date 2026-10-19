
from dataclasses import dataclass

from dns_toolkit.deployment.command_runner import CommandRunner


@dataclass(slots=True)
class VerificationResult:
        success: bool
        checks: dict[str, bool]
        messages: list[str]


class DeploymentVerifier:
        def __init__(
                self,
                command_runner: CommandRunner | None = None,
        ) -> None:
                self.command_runner = (
                        command_runner or CommandRunner()
                )

        def verify(
                self,
                zone_names: list[str],
        ) -> VerificationResult:
                checks: dict[str, bool] = {}
                messages: list[str] = []

                service_result = self.command_runner.run(
                        ["systemctl", "is-active", "bind9"]
                )
                checks["service_active"] = (
                        service_result.success
                        and service_result.stdout.strip() == "active"
                )
                messages.append(
                        "BIND service is active."
                        if checks["service_active"]
                        else "BIND service is not active: "
                        + service_result.output
                )

                for zone_name in zone_names:
                        result = self.command_runner.run(
                                [
                                        "dig",
                                        "+time=2",
                                        "+tries=1",
                                        "+short",
                                        "@127.0.0.1",
                                        zone_name,
                                        "SOA",
                                ],
                                timeout=5.0,
                        )

                        key = f"zone:{zone_name}"
                        checks[key] = (
                                result.success
                                and bool(result.stdout.strip())
                        )

                        messages.append(
                                f"Zone {zone_name} responded to an SOA query."
                                if checks[key]
                                else f"Zone {zone_name} did not return an SOA "
                                f"answer: {result.output}"
                        )

                return VerificationResult(
                        success=all(checks.values()) and bool(checks),
                        checks=checks,
                        messages=messages,
                )
