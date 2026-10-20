
import os
import shutil
import stat
from pathlib import Path


DEFAULT_HELPER_PATH = Path(
        "/usr/local/libexec/dns-toolkit-helper"
)


class HelperStatus:
        def __init__(
                self,
                helper_path: Path = DEFAULT_HELPER_PATH,
        ) -> None:
                self.helper_path = helper_path

        def inspect(self) -> dict[str, object]:
                pkexec_path = shutil.which("pkexec")
                result: dict[str, object] = {
                        "helper_path": str(self.helper_path),
                        "helper_exists": self.helper_path.is_file(),
                        "helper_root_owned": False,
                        "helper_not_writable_by_others": False,
                        "helper_executable": os.access(
                                self.helper_path,
                                os.X_OK,
                        ),
                        "pkexec_available": pkexec_path is not None,
                        "ready_for_review": False,
                }

                try:
                        metadata = self.helper_path.stat()
                except OSError:
                        return result

                result["helper_root_owned"] = metadata.st_uid == 0
                result["helper_not_writable_by_others"] = (
                        stat.S_ISREG(metadata.st_mode)
                        and metadata.st_mode & 0o022 == 0
                )

                result["ready_for_review"] = all(
                        [
                                result["helper_root_owned"],
                                result["helper_not_writable_by_others"],
                                result["helper_executable"],
                                result["pkexec_available"],
                        ]
                )

                return result
