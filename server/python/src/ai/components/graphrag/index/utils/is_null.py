"""定义is_null工具函数."""

import math
from typing import Any


def is_null(value: Any) -> bool:
    """检查值是否为null或NaN."""

    def is_none() -> bool:
        """
        处理none。

        Returns:
            处理结果。
        """
        return value is None

    def is_nan() -> bool:
        """
        处理nan。

        Returns:
            处理结果。
        """
        return isinstance(value, float) and math.isnan(value)

    return is_none() or is_nan()
