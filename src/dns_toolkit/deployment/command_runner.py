
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class CommandResult:
        command: list[str]
        returncode: int
        stdout: str
        stderr: str

        @property
        def success(self) -> bool:
                return self.returncode == 0

        @property
        def output(self) -> str:
                return "\n".join(
                        part
                        for part in (self.stdout, self.stderr)
                        if part
                )


class CommandRunner:
        def run(
                self,
                command: list[str],
                timeout: float = 30.0,
        ) -> CommandResult:
                if not command:
                        raise ValueError("Command cannot be empty.")

                executable = shutil.which(command[0])

                if executable is None:
                        return CommandResult(
                                command=command,
                                returncode=127,
                                stdout="",
                                stderr=f"Executable not found: {command[0]}",
                        )

                try:
                        result = subprocess.run(
                                [executable, *command[1:]],
                                capture_output=True,
                                text=True,
                                check=False,
                                timeout=timeout,
                        )
                except subprocess.TimeoutExpired as error:
                        stdout = error.stdout or ""
                        stderr = error.stderr or ""

                        if isinstance(stdout, bytes):
                                stdout = stdout.decode(errors="replace")

                        if isinstance(stderr, bytes):
                                stderr = stderr.decode(errors="replace")

                        return CommandResult(
                                command=command,
                                returncode=124,
                                stdout=stdout,
                                stderr=stderr or "Command timed out.",
                        )

                return CommandResult(
                        command=command,
                        returncode=result.returncode,
                        stdout=result.stdout,
                        stderr=result.stderr,
                )
