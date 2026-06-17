"""包含 'BasicMergeOperation', 'StringOperation', 'NumericOperation' and 'DetailedAttributeMergeOperation' 模型的模块."""

from dataclasses import dataclass
from enum import Enum


class BasicMergeOperation(str, Enum):
    """封装组件图谱检索增强生成中的BasicMergeOperation逻辑。"""

    Replace = "replace"
    Skip = "skip"


class StringOperation(str, Enum):
    """封装组件图谱检索增强生成中的StringOperation逻辑。"""

    Concat = "concat"
    Replace = "replace"
    Skip = "skip"


class NumericOperation(str, Enum):
    """封装组件图谱检索增强生成中的NumericOperation逻辑。"""

    Sum = "sum"
    Average = "average"
    Max = "max"
    Min = "min"
    Multiply = "multiply"
    Replace = "replace"
    Skip = "skip"


@dataclass
class DetailedAttributeMergeOperation:
    """封装组件图谱检索增强生成中的DetailedAttributeMergeOperation逻辑。"""

    operation: str  # StringOperation | NumericOperation

    # concat
    separator: str | None = None
    delimiter: str | None = None
    distinct: bool = False


AttributeMergeOperation = str | DetailedAttributeMergeOperation
