"""
配置辅助函数
"""

from typing import Any


def hyphen_to_underscore(key: Any) -> Any:
    """
    将字符串中的连字符 - 转换为下划线 _

    Args:
        key: 要转换的键，可能是字符串或其他类型

    Returns:
        转换后的结果，如果输入不是字符串则原样返回
    """
    if key is None:
        return None
    if isinstance(key, str):
        return key.replace("-", "_")
    return key


def convert_dict_hyphen_to_underscore(data: Any) -> Any:
    """
    递归地将字典中的键名从连字符形式转换为下划线形式

    Args:
        data: 要处理的数据，可能是字典、列表或其他类型

    Returns:
        处理后的数据
    """
    if data is None:
        return None

    if isinstance(data, dict):
        return {
            hyphen_to_underscore(k): convert_dict_hyphen_to_underscore(v)
            for k, v in data.items()
            if k is not None
        }
    elif isinstance(data, list):
        return [convert_dict_hyphen_to_underscore(item) for item in data]

    return data


def deep_merge_dict(base: dict, override: dict) -> dict:
    """
    深度合并两个字典

    Args:
        base: 基础字典
        override: 覆盖字典

    Returns:
        合并后的字典
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value

    return result
