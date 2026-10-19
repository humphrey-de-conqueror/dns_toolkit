
from dns_toolkit.models import DNSRecord, Zone
import ipaddress



def render_zone_declaration(zone: Zone) -> str:
        validate_zone_name(zone.name)

        normalized_name = zone.name.rstrip(".").lower()
        zone_file = f"/etc/bind/zones/db.{normalized_name}"

        return (
                f'zone "{normalized_name}" {{\n'
                f"        type master;\n"
                f'        file "{zone_file}";\n'
                f"}};"
        )



def render_zone_file(zone: Zone, serial: int = 1) -> str:
        validate_zone_name(zone.name)
        validate_zone_metadata(zone)
        validate_zone_records(zone)

        if serial < 1 or serial > 4294967295:
                raise ValueError(
                        f"Invalid SOA serial number: {serial}"
                )

        zone_name = zone.name.rstrip(".").lower() + "."
        nameserver = _absolute_domain(zone.nameserver)
        admin_email = _email_to_rname(zone.admin_email)

        lines = [
                f"$ORIGIN {zone_name}",
                "$TTL 3600",
                "",
                f"@ IN SOA {nameserver} {admin_email} (",
                f"        {serial} ; Serial",
                "        3600 ; Refresh",
                "        900  ; Retry",
                "        1209600 ; Expire",
                "        300  ; Negative Cache TTL",
                ")",
                "",
                f"@ IN NS {nameserver}",
        ]

        for record in zone.records:
                if _is_generated_nameserver_record(record, nameserver):
                        continue

                lines.append(_render_record(record))

        return "\n".join(lines) + "\n"



def render_zone_preview(zone: Zone, serial: int = 1) -> str:
        validate_zone_name(zone.name)
        validate_zone_metadata(zone)
        validate_zone_records(zone)

        if serial < 1 or serial > 4294967295:
                raise ValueError(
                        f"Invalid SOA serial number: {serial}"
                )

        declaration = render_zone_declaration(zone)
        zone_file = render_zone_file(zone, serial)

        return (
                "===== named.conf.local =====\n"
                f"{declaration}\n\n"
                f"===== db.{zone.name.rstrip('.')} =====\n"
                f"{zone_file}"
        )



def _absolute_domain(name: str) -> str:
        return name.rstrip(".").lower() + "."


def _email_to_rname(email: str) -> str:
        local_part, separator, domain = email.partition("@")

        if not separator or not local_part or not domain:
                raise ValueError(
                        f"Invalid SOA administrative email: {email}"
                )

        return f"{local_part}.{domain.rstrip('.').lower()}."


def _is_generated_nameserver_record(
        record: DNSRecord,
        nameserver: str,
) -> bool:
        return (
                record.name == "@"
                and record.record_type == "NS"
                and _absolute_domain(record.value) == nameserver
        )


def _render_record(record: DNSRecord) -> str:
        owner = record.name.rstrip(".") or "@"
        record_type = record.record_type.upper()
        value = record.value

        if record_type in {"CNAME", "NS"}:
                value = _absolute_domain(value)

        elif record_type == "MX":
                parts = value.split(maxsplit=1)

                if len(parts) != 2:
                        raise ValueError(
                                f"Invalid MX record value: {record.value}"
                        )

                value = f"{parts[0]} {_absolute_domain(parts[1])}"

        elif record_type == "TXT":
                escaped_value = (
                        value.replace("\\", "\\\\")
                        .replace('"', '\\"')
                )
                value = f'"{escaped_value}"'

        return f"{owner} {record.ttl} IN {record_type} {value}"


def validate_record(record: DNSRecord) -> None:
        supported_types = {"A", "AAAA", "CNAME", "MX", "NS", "TXT"}

        record_type = record.record_type.upper()

        validate_record_owner(record.name)
        validate_record_target(record)

        if record_type not in supported_types:
                raise ValueError(
                        f"Unsupported record type: {record.record_type}"
                )

        if (
                not isinstance(record.ttl, int)
                or isinstance(record.ttl, bool)
                or not 1 <= record.ttl <= 2147483647
        ):
                raise ValueError(
                        f"Invalid TTL for {record.name}: {record.ttl}"
                )

        if record_type == "A":
                try:
                        ipaddress.IPv4Address(record.value)
                except ipaddress.AddressValueError as error:
                        raise ValueError(
                                f"Invalid IPv4 address: {record.value}"
                        ) from error

        elif record_type == "AAAA":
                try:
                        ipaddress.IPv6Address(record.value)
                except ipaddress.AddressValueError as error:
                        raise ValueError(
                                f"Invalid IPv6 address: {record.value}"
                        ) from error

        elif record_type == "MX":
                parts = record.value.split(maxsplit=1)

                if len(parts) != 2:
                        raise ValueError(
                                f"Invalid MX record value: {record.value}"
                        )

                try:
                        preference = int(parts[0])
                except ValueError as error:
                        raise ValueError(
                                f"Invalid MX preference: {parts[0]}"
                        ) from error

                if not 0 <= preference <= 65535:
                        raise ValueError(
                                f"MX preference must be between 0 and 65535: "
                                f"{preference}"
                        )

                if not parts[1].strip():
                        raise ValueError(
                                f"Missing MX target: {record.value}"
                        )
        
        elif record_type == "TXT":
                validate_txt_value(record.value)


def validate_zone_records(zone: Zone) -> None:
        for record in zone.records:
                validate_record(record)

        records_by_owner: dict[str, list[DNSRecord]] = {}

        for record in zone.records:
                owner = record.name.rstrip(".").lower() or "@"
                records_by_owner.setdefault(owner, []).append(record)

        for owner, records in records_by_owner.items():
                if owner == "@" and any(
                        record.record_type.upper() == "CNAME"
                        for record in records
                ):
                        raise ValueError(
                                "A CNAME record cannot be configured at "
                                "the zone apex (@)."
                        )

                has_cname = any(
                        record.record_type.upper() == "CNAME"
                        for record in records
                )

                has_other_data = any(
                        record.record_type.upper() != "CNAME"
                        for record in records
                )

                if has_cname and has_other_data:
                        raise ValueError(
                                f"CNAME record at '{owner}' cannot coexist "
                                "with other record types."
                        )



def validate_zone_metadata(zone: Zone) -> None:
        if not zone.nameserver:
                raise ValueError("Nameserver cannot be empty.")

        validate_domain_name(zone.nameserver, "nameserver")

        if zone.admin_email.count("@") != 1:
                raise ValueError(
                        f"Invalid administrative email: {zone.admin_email}"
                )

        local_part, _, domain = zone.admin_email.partition("@")

        allowed_local_characters = (
                "abcdefghijklmnopqrstuvwxyz"
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "0123456789._+-"
        )

        if (
                not local_part
                or len(local_part) > 64
                or local_part.startswith(".")
                or local_part.endswith(".")
                or ".." in local_part
                or not all(
                        character in allowed_local_characters
                        for character in local_part
                )
        ):
                raise ValueError(
                        f"Invalid administrative email: {zone.admin_email}"
                )

        validate_domain_name(domain, "administrative email domain")
        _email_to_rname(zone.admin_email)



def validate_zone_name(name: str) -> None:
        normalized_name = name.rstrip(".")

        if not normalized_name or len(normalized_name) > 253:
                raise ValueError(f"Invalid zone name: {name}")

        labels = normalized_name.split(".")

        for label in labels:
                if (
                        not label
                        or len(label) > 63
                        or label.startswith("-")
                        or label.endswith("-")
                        or not all(
                                character in "abcdefghijklmnopqrstuvwxyz"
                                + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                                + "0123456789-"
                                for character in label
                        )
                ):
                        raise ValueError(f"Invalid zone name: {name}")


def validate_domain_name(name: str, field_name: str) -> None:
        normalized_name = name.rstrip(".")

        if not normalized_name or len(normalized_name) > 253:
                raise ValueError(f"Invalid {field_name}: {name}")

        for label in normalized_name.split("."):
                if (
                        not label
                        or len(label) > 63
                        or label.startswith("-")
                        or label.endswith("-")
                        or not all(
                                character
                                in "abcdefghijklmnopqrstuvwxyz"
                                + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                                + "0123456789-"
                                for character in label
                        )
                ):
                        raise ValueError(f"Invalid {field_name}: {name}")


def validate_record_owner(name: str) -> None:
        if name == "@":
                return

        if not name or name.startswith(".") or name.endswith("."):
                raise ValueError(f"Invalid record owner name: {name}")

        validate_domain_name(name, "record owner name")


def validate_record_target(record: DNSRecord) -> None:
        record_type = record.record_type.upper()

        if record_type in {"CNAME", "NS"}:
                validate_domain_name(record.value, f"{record_type} target")

        elif record_type == "MX":
                parts = record.value.split(maxsplit=1)

                if len(parts) == 2:
                        validate_domain_name(parts[1], "MX target")


def validate_txt_value(value: str) -> None:
        if not value:
                raise ValueError("TXT record value cannot be empty.")

        if len(value.encode("utf-8")) > 255:
                raise ValueError(
                        "TXT record value exceeds 255 bytes."
                )

        if any(ord(character) < 32 or ord(character) == 127 for character in value):
                raise ValueError(
                        "TXT record cannot contain control characters."
                )
