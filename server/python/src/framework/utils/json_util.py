"""
JSON 工具函数

提供增强的 JSON 处理功能。
"""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

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


def orjson_default(obj: Any) -> Any:
    """
    orjson 默认序列化函数

    - 优先调用对象的 __json__()（如 File 已实现），用于自定义序列化
    - 兼容 Pydantic BaseModel：使用 model_dump() 输出
    - 兼容 Enum：输出其 value
    - 兼容 set：转换为 list
    - 兼容 bytes/bytearray/memoryview：按 utf-8 解码
    """
    import enum

    # 对象自定义的 __json__ 钩子
    json_method = getattr(obj, "__json__", None)
    if callable(json_method):
        return json_method()

    # Pydantic BaseModel
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        return obj.model_dump()
    if hasattr(obj, "dict") and callable(obj.dict):
        return obj.dict()

    # Enum
    if isinstance(obj, enum.Enum):
        return obj.value

    # 集合类型
    if isinstance(obj, set):
        return list(obj)

    # 二进制
    if isinstance(obj, (bytes, bytearray, memoryview)):
        try:
            return bytes(obj).decode("utf-8")
        except Exception:
            # 不可解码则返回 base64 字符串，避免报错
            import base64

            return base64.b64encode(bytes(obj)).decode("ascii")

    # 其它不支持的类型
    raise TypeError(f"Type not serializable: {type(obj)!r}")
