from pathlib import Path

from dns_toolkit.bind_config import render_zone_file
from dns_toolkit.models import Zone


class ExportService:
        def export_zone(
                self,
                zone: Zone,
                output_directory: Path,
                serial: int = 1,
        ) -> list[Path]:
                normalized_name = zone.name.rstrip(".").lower()

                zone_directory = output_directory / "zones"
                zone_directory.mkdir(
                        parents=True,
                        exist_ok=True,
                )

                declaration_path = (
                        output_directory / f"{normalized_name}.conf"
                )
                zone_file_path = (
                        zone_directory / f"db.{normalized_name}"
                )

                declaration = (
                        f'zone "{normalized_name}" {{\n'
                        "        type master;\n"
                        f'        file "zones/db.{normalized_name}";\n'
                        "};\n"
                )

                zone_content = render_zone_file(
                        zone,
                        serial=serial,
                )

                declaration_path.write_text(
                        declaration,
                        encoding="utf-8",
                )
                zone_file_path.write_text(
                        zone_content,
                        encoding="utf-8",
                )

                return [
                        declaration_path,
                        zone_file_path,
                ]