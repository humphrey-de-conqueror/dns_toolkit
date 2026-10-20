
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class AppSettings:
        active_target_id: str = "local"
        bind_config_path: str = "/etc/bind/named.conf"
        bind_service_name: str = "bind9"
        zone_file_directory: str = "/etc/bind/zones"
        export_directory: str = "~/dns-toolkit-exports"
        default_ttl: int = 3600


class SettingsRepository:
        def __init__(
                self,
                settings_path: Path | None = None,
        ) -> None:
                self.settings_path = (
                        settings_path
                        or Path.home()
                        / ".config"
                        / "dns-toolkit"
                        / "settings.json"
                )

        @staticmethod
        def _validate(settings: AppSettings) -> None:
                if not settings.active_target_id.strip():
                        raise ValueError(
                                "Active target ID cannot be empty."
                        )

                if not settings.bind_service_name.strip():
                        raise ValueError(
                                "BIND service name cannot be empty."
                        )

                for field_name, raw_path in (
                        ("bind_config_path", settings.bind_config_path),
                        (
                                "zone_file_directory",
                                settings.zone_file_directory,
                        ),
                        ("export_directory", settings.export_directory),
                ):
                        if not raw_path.strip():
                                raise ValueError(
                                        f"{field_name} cannot be empty."
                                )

                if settings.default_ttl < 1 or settings.default_ttl > 2147483647:
                        raise ValueError(
                                "Default TTL must be a positive 32-bit integer."
                        )

                if not Path(settings.bind_config_path).is_absolute():
                        raise ValueError(
                                "BIND configuration path must be absolute."
                        )

                if not Path(
                        settings.zone_file_directory
                ).is_absolute():
                        raise ValueError(
                                "Zone file directory must be absolute."
                        )

        def load(self) -> AppSettings:
                if not self.settings_path.exists():
                        return AppSettings()

                data = json.loads(
                        self.settings_path.read_text(encoding="utf-8")
                )

                if not isinstance(data, dict):
                        raise ValueError(
                                "Settings file must contain a JSON object."
                        )

                defaults = asdict(AppSettings())

                for key in defaults:
                        if key in data:
                                defaults[key] = data[key]

                settings = AppSettings(**defaults)
                self._validate(settings)
                return settings

        def save(self, settings: AppSettings) -> None:
                self._validate(settings)

                self.settings_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                )

                temporary_path = self.settings_path.with_suffix(".tmp")
                temporary_path.write_text(
                        json.dumps(asdict(settings), indent=4) + "\n",
                        encoding="utf-8",
                )
                temporary_path.replace(self.settings_path)

        def update(self, **changes: object) -> AppSettings:
                settings = self.load()
                allowed_fields = set(asdict(settings))

                unknown_fields = set(changes) - allowed_fields

                if unknown_fields:
                        raise ValueError(
                                "Unknown settings: "
                                + ", ".join(sorted(unknown_fields))
                        )

                for key, value in changes.items():
                        setattr(settings, key, value)

                self.save(settings)
                return settings

        def reset(self) -> AppSettings:
                settings = AppSettings()
                self.save(settings)
                return settings
