
import json
from dataclasses import dataclass
from pathlib import Path

from dns_toolkit.deployment.plan import DeploymentPlan


@dataclass(slots=True)
class DeploymentManifest:
        config_path: Path
        files: dict[Path, str]
        service_name: str = "bind9"

        @classmethod
        def from_plan(
                cls,
                plan: DeploymentPlan,
        ) -> "DeploymentManifest":
                if not plan.is_valid:
                        raise ValueError(
                                "Cannot create a manifest from an invalid "
                                "deployment plan."
                        )

                return cls(
                        config_path=plan.config_path,
                        files=dict(plan.files),
                )

        def validate(self) -> list[str]:
                errors: list[str] = []
                config_path = Path("/etc/bind/named.conf")
                include_path = Path(
                        "/etc/bind/dns-toolkit-zones.conf"
                )
                zone_directory = Path("/etc/bind/zones")

                if self.config_path != config_path:
                        errors.append(
                                f"Unsupported configuration path: "
                                f"{self.config_path}"
                        )

                if self.service_name != "bind9":
                        errors.append(
                                f"Unsupported service: {self.service_name}"
                        )

                if config_path not in self.files:
                        errors.append(
                                "Manifest must include candidate named.conf."
                        )

                if include_path not in self.files:
                        errors.append(
                                "Manifest must include the managed zone file."
                        )

                if not self.files:
                        errors.append("Manifest contains no files.")

                for destination in self.files:
                        if destination == config_path:
                                continue

                        if destination == include_path:
                                continue

                        if (
                                destination.parent == zone_directory
                                and destination.name.startswith("db.")
                                and destination.name not in {"db.", "db.."}
                        ):
                                continue

                        errors.append(
                                f"Destination is not permitted: {destination}"
                        )

                return errors

        def write(self, path: Path) -> None:
                errors = self.validate()

                if errors:
                        raise ValueError("\n".join(errors))

                payload = {
                        "version": 1,
                        "config_path": str(self.config_path),
                        "service_name": self.service_name,
                        "files": [
                                {
                                        "destination": str(destination),
                                        "content": content,
                                }
                                for destination, content in self.files.items()
                        ],
                }

                path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                )

                temporary_path = path.with_suffix(".tmp")
                temporary_path.write_text(
                        json.dumps(payload, indent=2) + "\n",
                        encoding="utf-8",
                )
                temporary_path.replace(path)

        @classmethod
        def read(cls, path: Path) -> "DeploymentManifest":
                payload = json.loads(
                        path.read_text(encoding="utf-8")
                )

                if payload.get("version") != 1:
                        raise ValueError(
                                "Unsupported manifest version."
                        )

                entries = payload.get("files")

                if not isinstance(entries, list):
                        raise ValueError(
                                "Manifest files must be a list."
                        )

                files: dict[Path, str] = {}

                for entry in entries:
                        if not isinstance(entry, dict):
                                raise ValueError(
                                        "Invalid manifest entry."
                                )

                        destination = Path(entry["destination"])
                        content = entry["content"]

                        if not isinstance(content, str):
                                raise ValueError(
                                        "Manifest file content must be text."
                                )

                        if destination in files:
                                raise ValueError(
                                        f"Duplicate destination: {destination}"
                                )

                        files[destination] = content

                manifest = cls(
                        config_path=Path(payload["config_path"]),
                        files=files,
                        service_name=payload["service_name"],
                )

                errors = manifest.validate()

                if errors:
                        raise ValueError("\n".join(errors))

                return manifest
