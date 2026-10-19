
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DeploymentPlan:
        target_name: str
        config_path: Path
        files: dict[Path, str]
        validation_errors: list[str]

        @property
        def is_valid(self) -> bool:
                return not self.validation_errors

        @property
        def file_count(self) -> int:
                return len(self.files)
