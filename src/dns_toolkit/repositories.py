
import json
import os
import tempfile
from pathlib import Path

from dns_toolkit.models import DNSRecord, Zone, ZoneType


class ZoneRepository:
        SCHEMA_VERSION = 1

        def __init__(
                self,
                storage_path: Path | None = None,
        ) -> None:
                self.storage_path = (
                        storage_path
                        or Path.home()
                        / ".config"
                        / "dns-toolkit"
                        / "zones.json"
                )

        def list_zones(self) -> list[Zone]:
                payload = self._read_payload()
                return [
                        self._zone_from_dict(item)
                        for item in payload["zones"]
                ]

        def get_zone(self, zone_name: str) -> Zone | None:
                normalized_name = self._normalize_zone_name(zone_name)

                for zone in self.list_zones():
                        if self._normalize_zone_name(zone.name) == normalized_name:
                                return zone

                return None

        def add_zone(self, zone: Zone) -> None:
                zones = self.list_zones()
                normalized_name = self._normalize_zone_name(zone.name)

                if any(
                        self._normalize_zone_name(existing.name)
                        == normalized_name
                        for existing in zones
                ):
                        raise ValueError(
                                f"Zone already exists: {zone.name}"
                        )

                zones.append(zone)
                self._write_zones(zones)

        def delete_zone(self, zone_name: str) -> None:
                normalized_name = self._normalize_zone_name(zone_name)
                zones = self.list_zones()
                remaining = [
                        zone
                        for zone in zones
                        if self._normalize_zone_name(zone.name)
                        != normalized_name
                ]

                if len(remaining) == len(zones):
                        raise ValueError(
                                f"Zone does not exist: {zone_name}"
                        )

                self._write_zones(remaining)

        def add_record(
                self,
                zone_name: str,
                record: DNSRecord,
        ) -> None:
                zone = self._require_zone(zone_name)
                zone.records.append(record)
                self._replace_zone(zone)

        def update_record(
                self,
                zone_name: str,
                record_index: int,
                record: DNSRecord,
        ) -> None:
                zone = self._require_zone(zone_name)

                if not 0 <= record_index < len(zone.records):
                        raise IndexError(
                                f"Record index out of range: {record_index}"
                        )

                zone.records[record_index] = record
                self._replace_zone(zone)

        def delete_record(
                self,
                zone_name: str,
                record_index: int,
        ) -> None:
                zone = self._require_zone(zone_name)

                if not 0 <= record_index < len(zone.records):
                        raise IndexError(
                                f"Record index out of range: {record_index}"
                        )

                del zone.records[record_index]
                self._replace_zone(zone)

        def _require_zone(self, zone_name: str) -> Zone:
                zone = self.get_zone(zone_name)

                if zone is None:
                        raise ValueError(
                                f"Zone does not exist: {zone_name}"
                        )

                return zone

        def _replace_zone(self, updated_zone: Zone) -> None:
                zones = self.list_zones()
                normalized_name = self._normalize_zone_name(
                        updated_zone.name
                )

                for index, zone in enumerate(zones):
                        if (
                                self._normalize_zone_name(zone.name)
                                == normalized_name
                        ):
                                zones[index] = updated_zone
                                self._write_zones(zones)
                                return

                raise ValueError(
                        f"Zone does not exist: {updated_zone.name}"
                )

        def _read_payload(self) -> dict[str, object]:
                if not self.storage_path.exists():
                        return {
                                "version": self.SCHEMA_VERSION,
                                "zones": [],
                        }

                try:
                        payload = json.loads(
                                self.storage_path.read_text(
                                        encoding="utf-8"
                                )
                        )
                except json.JSONDecodeError as error:
                        raise ValueError(
                                f"Invalid zone storage JSON: {error}"
                        ) from error

                if not isinstance(payload, dict):
                        raise ValueError(
                                "Zone storage must contain a JSON object."
                        )

                stored_version = payload.get(
                        "version",
                        payload.get("schema_version"),
                )

                if stored_version != self.SCHEMA_VERSION:
                        raise ValueError(
                                "Unsupported zone storage version."
                        )

                zones = payload.get("zones")

                if not isinstance(zones, list):
                        raise ValueError(
                                "Zone storage must contain a zones list."
                        )

                if not all(isinstance(item, dict) for item in zones):
                        raise ValueError(
                                "Each stored zone must be a JSON object."
                        )

                return payload

        def _write_zones(self, zones: list[Zone]) -> None:
                self.storage_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                )

                payload = {
                        "version": self.SCHEMA_VERSION,
                        "zones": [
                                self._zone_to_dict(zone)
                                for zone in zones
                        ],
                }

                descriptor, temporary_name = tempfile.mkstemp(
                        prefix="zones-",
                        suffix=".tmp",
                        dir=self.storage_path.parent,
                )
                temporary_path = Path(temporary_name)

                try:
                        with os.fdopen(
                                descriptor,
                                "w",
                                encoding="utf-8",
                        ) as temporary_file:
                                json.dump(
                                        payload,
                                        temporary_file,
                                        indent=4,
                                )
                                temporary_file.write("\n")
                                temporary_file.flush()
                                os.fsync(temporary_file.fileno())

                        temporary_path.replace(self.storage_path)

                except Exception:
                        temporary_path.unlink(missing_ok=True)
                        raise

        @staticmethod
        def _zone_to_dict(zone: Zone) -> dict[str, object]:
                return {
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

        @staticmethod
        def _zone_from_dict(data: dict[str, object]) -> Zone:
                raw_records = data.get("records", [])

                if not isinstance(raw_records, list):
                        raise ValueError(
                                "Stored zone records must be a list."
                        )

                records: list[DNSRecord] = []

                for item in raw_records:
                        if not isinstance(item, dict):
                                raise ValueError(
                                        "Each stored record must be an object."
                                )

                        records.append(
                                DNSRecord(
                                        name=str(item["name"]),
                                        record_type=str(
                                                item["record_type"]
                                        ),
                                        value=str(item["value"]),
                                        ttl=int(item.get("ttl", 3600)),
                                )
                        )

                raw_zone_type = str(
                        data.get("zone_type", ZoneType.PRIMARY.value)
                )

                try:
                        zone_type = ZoneType(raw_zone_type)
                except ValueError as error:
                        raise ValueError(
                                f"Unsupported zone type: {raw_zone_type}"
                        ) from error

                return Zone(
                        name=str(data["name"]),
                        nameserver=str(data["nameserver"]),
                        admin_email=str(data["admin_email"]),
                        zone_type=zone_type,
                        records=records,
                )

        @staticmethod
        def _normalize_zone_name(name: str) -> str:
                return name.rstrip(".").lower()
