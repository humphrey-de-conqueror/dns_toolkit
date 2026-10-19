
from dns_toolkit.deployment.base import DeploymentTarget
from dns_toolkit.deployment.local_bind import LocalBindBackend


class TargetService:
        def __init__(self) -> None:
                self.targets = {
                        "local": DeploymentTarget(
                                target_id="local",
                                name="Local BIND 9",
                                target_type="local",
                                host="localhost",
                        )
                }
                self.active_target_id = "local"

        def list_targets(self) -> list[DeploymentTarget]:
                return list(self.targets.values())

        def get_active_target(self) -> DeploymentTarget:
                return self.targets[self.active_target_id]

        def select_target(self, target_id: str) -> DeploymentTarget:
                if target_id not in self.targets:
                        raise ValueError(
                                f"Unknown deployment target: {target_id}"
                        )

                self.active_target_id = target_id
                return self.targets[target_id]

        def create_backend(self) -> LocalBindBackend:
                target = self.get_active_target()

                if target.target_type != "local":
                        raise NotImplementedError(
                                "This deployment target is not implemented."
                        )

                return LocalBindBackend()
