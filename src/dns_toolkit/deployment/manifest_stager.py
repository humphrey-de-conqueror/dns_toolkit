
import os
import tempfile
from pathlib import Path

from dns_toolkit.deployment.manifest import DeploymentManifest


class ManifestStager:
        def __init__(
                self,
                staging_directory: Path | None = None,
        ) -> None:
                self.staging_directory = (
                        staging_directory
                        or Path.home()
                        / ".local"
                        / "state"
                        / "dns-toolkit"
                        / "staging"
                )

        def stage(
                self,
                manifest: DeploymentManifest,
        ) -> Path:
                errors = manifest.validate()

                if errors:
                        raise ValueError("\n".join(errors))

                self.staging_directory.mkdir(
                        parents=True,
                        exist_ok=True,
                        mode=0o700,
                )

                if self.staging_directory.is_symlink():
                        raise ValueError(
                                "Staging directory cannot be a symlink."
                        )

                os.chmod(self.staging_directory, 0o700)

                descriptor, filename = tempfile.mkstemp(
                        prefix="deployment-",
                        suffix=".json",
                        dir=self.staging_directory,
                )
                os.close(descriptor)

                manifest_path = Path(filename)

                try:
                        manifest.write(manifest_path)
                        os.chmod(manifest_path, 0o600)
                except Exception:
                        manifest_path.unlink(missing_ok=True)
                        raise

                return manifest_path

        @staticmethod
        def cleanup(manifest_path: Path) -> None:
                manifest_path.unlink(missing_ok=True)
