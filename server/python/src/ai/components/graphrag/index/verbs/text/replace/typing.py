"""包含 'Replacement' 模型的模块."""

from dataclasses import dataclass


@dataclass
class Replacement:
    """封装组件图谱检索增强生成中的Replacement逻辑。"""

    pattern: str
    replacement: str
