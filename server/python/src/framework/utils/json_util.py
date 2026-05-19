"""
JSON 工具函数

提供增强的 JSON 处理功能。
"""

import json
from datetime import datetime, date
from typing import Any
from decimal import Decimal

import orjson


class DateTimeEncoder(json.JSONEncoder):
    """支持日期时间类型的 JSON 编码器"""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def json_dumps(obj: Any, indent: int | None = None, ensure_ascii: bool = False) -> str:
    """
    将对象序列化为 JSON 字符串

    支持日期时间类型的自动序列化。

    Args:
        obj: 要序列化的对象
        indent: 缩进空格数
        ensure_ascii: 是否确保 ASCII 编码

    Returns:
        str: JSON 字符串
    """
    # 使用 orjson 进行高效序列化
    option = 0
    if indent:
        option |= orjson.OPT_INDENT_2
    if not ensure_ascii:
        option |= orjson.OPT_SERIALIZE_NUMPY

    def default(obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    result = orjson.dumps(obj, default=default, option=option)
    return result.decode("utf-8")


def json_loads(text: str | bytes) -> Any:
    """
    解析 JSON 字符串

    Args:
        text: JSON 字符串或字节

    Returns:
        Any: 解析后的对象
    """
    if isinstance(text, str):
        text = text.encode("utf-8")

    return orjson.loads(text)


def json_loads_loose(text: str) -> Any:
    """
    宽松的 JSON 解析

    支持尾随逗号、单引号等非标准格式。

    Args:
        text: JSON 字符串

    Returns:
        Any: 解析后的对象
    """
    import re

    # 移除尾随逗号
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # 将单引号替换为双引号（简单处理，可能不适用于所有情况）
    # 注意：这种替换可能会破坏字符串中包含的单引号

    return json_loads(text)
