
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DeploymentTarget:
        target_id: str
        name: str
        target_type: str
        host: str = "localhost"
        enabled: bool = True


@dataclass(slots=True)
class DeploymentResult:
        success: bool
        message: str
        changed_files: list[Path]
        backup_directory: Path | None = None
        command_output: str = ""


class DeploymentBackend(ABC):
        @abstractmethod
        def inspect(self) -> dict[str, object]:
                """Return information about the deployment environment."""

        @abstractmethod
        def validate(self, config_path: Path) -> tuple[bool, str]:
                """Validate a candidate BIND configuration."""

        @abstractmethod
        def deploy(
                self,
                config_path: Path,
                zone_files: dict[Path, str],
                confirmed: bool,
        ) -> DeploymentResult:
                """Deploy configuration after explicit user confirmation."""
