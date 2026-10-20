
import shutil

from dns_toolkit.deployment.command_runner import CommandRunner


class BindService:
        def __init__(
                self,
                service_name: str = "bind9",
                command_runner: CommandRunner | None = None,
        ) -> None:
                self.service_name = service_name
                self.command_runner = (
                        command_runner or CommandRunner()
                )

        def get_executables(self) -> dict[str, str | None]:
                names = [
                        "named",
                        "named-checkconf",
                        "named-checkzone",
                        "rndc",
                        "dig",
                        "systemctl",
                ]

                return {
                        name: shutil.which(name)
                        for name in names
                }

        def get_service_status(self) -> dict[str, str]:
                systemctl = shutil.which("systemctl")

                if systemctl is None:
                        return {
                                "state": "unavailable",
                                "substate": "unknown",
                                "message": "systemctl is not installed.",
                        }

                result = self.command_runner.run(
                        [
                                systemctl,
                                "show",
                                self.service_name,
                                "--property=ActiveState",
                                "--property=SubState",
                                "--no-pager",
                        ]
                )

                if not result.success:
                        return {
                                "state": "unknown",
                                "substate": "unknown",
                                "message": (
                                        result.output
                                        or "Could not query BIND service status."
                                ),
                        }

                properties: dict[str, str] = {}

                for line in result.stdout.splitlines():
                        key, separator, value = line.partition("=")

                        if separator:
                                properties[key] = value

                state = properties.get("ActiveState", "unknown")
                substate = properties.get("SubState", "unknown")

                return {
                        "state": state,
                        "substate": substate,
                        "message": (
                                f"{self.service_name}: {state} ({substate})"
                        ),
                }

        def perform_service_action(
                self,
                action: str,
        ) -> tuple[bool, str]:
                allowed_actions = {
                        "start",
                        "stop",
                        "restart",
                        "reload",
                }

                if action not in allowed_actions:
                        return False, f"Unsupported service action: {action}"

                systemctl = shutil.which("systemctl")

                if systemctl is None:
                        return False, "systemctl is not installed."

                return False, (
                        "Service actions are disabled in the unprivileged "
                        "application. Use the future restricted privileged "
                        "helper after its security review."
                )
