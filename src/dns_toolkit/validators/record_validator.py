
from dns_toolkit.bind_config import validate_record
from dns_toolkit.models import DNSRecord


def validate_dns_record(record: DNSRecord) -> list[str]:
        try:
                validate_record(record)
        except ValueError as error:
                return [str(error)]

        return []
