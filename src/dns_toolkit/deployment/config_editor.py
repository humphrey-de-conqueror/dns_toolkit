
import re
from pathlib import Path


MANAGED_INCLUDE = 'include "/etc/bind/dns-toolkit-zones.conf";'


def build_candidate_config(
        source: str,
        include_line: str = MANAGED_INCLUDE,
) -> str:
        active_lines = [
                line.strip()
                for line in source.splitlines()
                if not line.lstrip().startswith("//")
                and not line.lstrip().startswith("#")
        ]

        if any(
                re.fullmatch(
                        r'include\s+["\']/etc/bind/dns-toolkit-zones\.conf["\'];?',
                        line,
                )
                for line in active_lines
        ):
                return source if source.endswith("\n") else source + "\n"

        if not source.strip():
                raise ValueError(
                        "The existing BIND configuration is empty."
                )

        return source.rstrip() + "\n\n" + include_line + "\n"


def read_candidate_config(config_path: Path) -> str:
        if not config_path.is_absolute():
                raise ValueError(
                        "The BIND configuration path must be absolute."
                )

        if not config_path.is_file():
                raise FileNotFoundError(
                        f"BIND configuration not found: {config_path}"
                )

        return build_candidate_config(
                config_path.read_text(encoding="utf-8")
        )
