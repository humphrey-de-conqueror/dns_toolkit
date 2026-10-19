
from dns_toolkit.bind_config import (
        validate_zone_metadata,
        validate_zone_name,
        validate_zone_records,
)
from dns_toolkit.models import Zone


def validate_zone(zone: Zone) -> list[str]:
        errors = []

        try:
                validate_zone_name(zone.name)
        except ValueError as error:
                errors.append(str(error))

        try:
                validate_zone_metadata(zone)
        except ValueError as error:
                errors.append(str(error))

        try:
                validate_zone_records(zone)
        except ValueError as error:
                errors.append(str(error))

        return errors
