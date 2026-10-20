
from dataclasses import dataclass, field
from enum import StrEnum


class ZoneType(StrEnum):
        PRIMARY = "Primary"


@dataclass(slots=True)
class DNSRecord:
        name: str
        record_type: str
        value: str
        ttl: int = 3600


@dataclass(slots=True)
class Zone:
        name: str
        nameserver: str
        admin_email: str
        zone_type: ZoneType = ZoneType.PRIMARY
        records: list[DNSRecord] = field(default_factory=list)
