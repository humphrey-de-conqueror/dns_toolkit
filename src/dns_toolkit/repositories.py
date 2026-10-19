
import json
from pathlib import Path

from dns_toolkit.models import DNSRecord, Zone, ZoneType


class ZoneRepository:
        def __init__(self, storage_path: Path | None = None) -> None:
                self._storage_path = (
                        storage_path
                        if storage_path is not None
                        else Path.home()
                        / ".config"
                        / "dns-toolkit"
                        / "zones.json"
                )
                self._zones: dict[str, Zone] = {}
                self._load_zones()

        def list_zones(self) -> list[Zone]:
                return list(self._zones.values())

        def get_zone(self, name: str) -> Zone | None:
                return self._zones.get(self._normalize_name(name))

        def add_zone(self, zone: Zone) -> None:
                key = self._normalize_name(zone.name)

                if key in self._zones:
                        raise ValueError(f"Zone already exists: {zone.name}")

                updated_zones = self._zones.copy()
                updated_zones[key] = zone

                self._save_zones(updated_zones)
                self._zones = updated_zones

        def delete_zone(self, name: str) -> bool:
                key = self._normalize_name(name)

                if key not in self._zones:
                        return False

                updated_zones = self._zones.copy()
                del updated_zones[key]

                self._save_zones(updated_zones)
                self._zones = updated_zones
                return True

        def add_record(self, zone_name: str, record: DNSRecord) -> None:
                key = self._normalize_name(zone_name)
                existing_zone = self._zones.get(key)

                if existing_zone is None:
                        raise ValueError(f"Zone does not exist: {zone_name}")

                for existing_record in existing_zone.records:
                        if (
                                existing_record.name.lower() == record.name.lower()
                                and existing_record.record_type == record.record_type
                                and existing_record.value == record.value
                        ):
                                raise ValueError(
                                        f"Record already exists in zone "
                                        f"'{existing_zone.name}'."
                                )

                updated_zone = Zone(
                        name=existing_zone.name,
                        nameserver=existing_zone.nameserver,
                        admin_email=existing_zone.admin_email,
                        zone_type=existing_zone.zone_type,
                        records=[*existing_zone.records, record],
                )

                updated_zones = self._zones.copy()
                updated_zones[key] = updated_zone

                self._save_zones(updated_zones)
                self._zones = updated_zones
	

        def delete_record(
                self,
                zone_name: str,
                record: DNSRecord,
        ) -> bool:
                key = self._normalize_name(zone_name)
                existing_zone = self._zones.get(key)

                if existing_zone is None:
                        raise ValueError(f"Zone does not exist: {zone_name}")

                record_index = next(
                        (
                                index
                                for index, existing_record
                                in enumerate(existing_zone.records)
                                if existing_record is record
                        ),
                        None,
                )

                if record_index is None:
                        record_index = next(
                                (
                                        index
                                        for index, existing_record
                                        in enumerate(existing_zone.records)
                                        if existing_record == record
                                ),
                                None,
                        )

                if record_index is None:
                        return False

                updated_records = list(existing_zone.records)
                del updated_records[record_index]

                updated_zone = Zone(
                        name=existing_zone.name,
                        nameserver=existing_zone.nameserver,
                        admin_email=existing_zone.admin_email,
                        zone_type=existing_zone.zone_type,
                        records=updated_records,
                )

                updated_zones = self._zones.copy()
                updated_zones[key] = updated_zone

                self._save_zones(updated_zones)
                self._zones = updated_zones
                return True


        def update_record(
                self,
                zone_name: str,
                old_record: DNSRecord,
                new_record: DNSRecord,
        ) -> None:
                key = self._normalize_name(zone_name)
                existing_zone = self._zones.get(key)

                if existing_zone is None:
                        raise ValueError(f"Zone does not exist: {zone_name}")

                record_index = next(
                        (
                                index
                                for index, record
                                in enumerate(existing_zone.records)
                                if record == old_record
                        ),
                        None,
                )

                if record_index is None:
                        raise ValueError("The original record no longer exists.")

                for index, record in enumerate(existing_zone.records):
                        if index == record_index:
                                continue

                        if (
                                record.name.lower() == new_record.name.lower()
                                and record.record_type == new_record.record_type
                                and record.value == new_record.value
                        ):
                                raise ValueError(
                                        "An identical record already exists."
                                )

                updated_records = list(existing_zone.records)
                updated_records[record_index] = new_record

                updated_zone = Zone(
                        name=existing_zone.name,
                        nameserver=existing_zone.nameserver,
                        admin_email=existing_zone.admin_email,
                        zone_type=existing_zone.zone_type,
                        records=updated_records,
                )

                updated_zones = self._zones.copy()
                updated_zones[key] = updated_zone

                self._save_zones(updated_zones)
                self._zones = updated_zones


        def _load_zones(self) -> None:
                if not self._storage_path.exists():
                        return

                try:
                        data = json.loads(
                                self._storage_path.read_text(encoding="utf-8")
                        )

                        if data.get("schema_version") != 1:
                                raise ValueError(
                                        "Unsupported zones file schema version."
                                )

                        loaded_zones: dict[str, Zone] = {}

                        for item in data["zones"]:
                                records = [
                                        DNSRecord(
                                                name=record["name"],
                                                record_type=record["record_type"],
                                                value=record["value"],
                                                ttl=record.get("ttl", 3600),
                                        )
                                        for record in item.get("records", [])
                                ]

                                zone = Zone(
                                        name=item["name"],
                                        nameserver=item["nameserver"],
                                        admin_email=item["admin_email"],
                                        zone_type=ZoneType(item["zone_type"]),
                                        records=records,
                                )

                                key = self._normalize_name(zone.name)

                                if key in loaded_zones:
                                        raise ValueError(
                                                f"Duplicate zone in file: {zone.name}"
                                        )

                                loaded_zones[key] = zone

                        self._zones = loaded_zones

                except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                        raise RuntimeError(
                                f"Unable to load zones from "
                                f"{self._storage_path}: {exc}"
                        ) from exc

        def _save_zones(self, zones: dict[str, Zone]) -> None:
                data = {
                        "schema_version": 1,
                        "zones": [
                                {
                                        "name": zone.name,
                                        "nameserver": zone.nameserver,
                                        "admin_email": zone.admin_email,
                                        "zone_type": zone.zone_type.value,
                                        "records": [
                                                {
                                                        "name": record.name,
                                                        "record_type": record.record_type,
                                                        "value": record.value,
                                                        "ttl": record.ttl,
                                                }
                                                for record in zone.records
                                        ],
                                }
                                for zone in zones.values()
                        ],
                }

                try:
                        self._storage_path.parent.mkdir(
                                parents=True,
                                exist_ok=True,
                        )

                        temporary_path = self._storage_path.with_suffix(".tmp")
                        temporary_path.write_text(
                                json.dumps(data, indent=4) + "\n",
                                encoding="utf-8",
                        )
                        temporary_path.replace(self._storage_path)

                except OSError as exc:
                        raise RuntimeError(
                                f"Unable to save zones to "
                                f"{self._storage_path}: {exc}"
                        ) from exc

        @staticmethod
        def _normalize_name(name: str) -> str:
                return name.rstrip(".").lower()
