# 目前使用此方法而不是包装器
"""包含'NodePosition'模型的模块."""

from dataclasses import dataclass


@dataclass
class NodePosition:
    """节点位置类定义."""

    label: str
    cluster: str
    size: float

    x: float
    y: float
    z: float | None = None

    def to_pandas(self) -> tuple[str, float, float, str, float]:
        """转换为pandas方法定义."""
        return self.label, self.x, self.y, self.cluster, self.size


GraphLayout = list[NodePosition]
