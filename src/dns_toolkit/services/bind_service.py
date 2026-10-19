
import shutil
import subprocess


class BindService:
        def __init__(self, service_name: str = "bind9") -> None:
                self.service_name = service_name

        def get_executables(self) -> dict[str, str | None]:
                names = (
                        "named",
                        "named-checkconf",
                        "named-checkzone",
                        "rndc",
                        "dig",
                )

                return {
                        name: shutil.which(name)
                        for name in names
                }

        def get_service_status(self) -> dict[str, str]:
                if shutil.which("systemctl") is None:
                        return {
                                "state": "unknown",
                                "message": "systemctl is unavailable.",
                        }

                result = subprocess.run(
                        [
                                "systemctl",
                                "show",
                                self.service_name,
                                "--property=ActiveState",
                                "--property=SubState",
                                "--no-pager",
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                )

                if result.returncode != 0:
                        return {
                                "state": "unknown",
                                "message": (
                                        result.stderr.strip()
                                        or "Unable to inspect BIND service."
                                ),
                        }

                properties = {}

                for line in result.stdout.splitlines():
                        key, separator, value = line.partition("=")

                        if separator:
                                properties[key] = value

                return {
                        "state": properties.get("ActiveState", "unknown"),
                        "substate": properties.get("SubState", "unknown"),
                        "message": "Service status retrieved.",
                }

        def perform_service_action(self, action: str) -> tuple[bool, str]:
                allowed_actions = {"start", "stop", "restart", "reload"}

                if action not in allowed_actions:
                        return False, f"Unsupported service action: {action}"

                if shutil.which("systemctl") is None:
                        return False, "systemctl is unavailable."

                result = subprocess.run(
                        ["systemctl", action, self.service_name],
                        capture_output=True,
                        text=True,
                        check=False,
                )

                output = "\n".join(
                        part
                        for part in (result.stdout, result.stderr)
                        if part
                )

                return (
                        result.returncode == 0,
                        output or f"systemctl {action} completed.",
                )
