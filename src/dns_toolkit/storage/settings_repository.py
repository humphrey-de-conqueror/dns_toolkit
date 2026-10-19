
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
        def __init__(self, settings_path: Path | None = None) -> None:
                self.settings_path = (
                        settings_path
                        or Path.home()
                        / ".config"
                        / "dns-toolkit"
                        / "settings.json"
                )

        def load(self) -> AppSettings:
                if not self.settings_path.exists():
                        return AppSettings()

                data = json.loads(
                        self.settings_path.read_text(encoding="utf-8")
                )

                defaults = asdict(AppSettings())

                for key in defaults:
                        if key in data:
                                defaults[key] = data[key]

                return AppSettings(**defaults)

        def save(self, settings: AppSettings) -> None:
                self.settings_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                )

                temporary_path = self.settings_path.with_suffix(".tmp")

                temporary_path.write_text(
                        json.dumps(
                                asdict(settings),
                                indent=4,
                        )
                        + "\n",
                        encoding="utf-8",
                )

                temporary_path.replace(self.settings_path)

        def update(self, **changes: object) -> AppSettings:
                settings = self.load()

                for key, value in changes.items():
                        if not hasattr(settings, key):
                                raise ValueError(
                                        f"Unknown setting: {key}"
                                )

                        setattr(settings, key, value)

                self.save(settings)
                return settings

        def reset(self) -> AppSettings:
                settings = AppSettings()
                self.save(settings)
                return settings
