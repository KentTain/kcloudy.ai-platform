"""
配置辅助函数
"""

from typing import Any


def hyphen_to_underscore(key: Any) -> Any:
    """将字符串中的连字符 - 转换为下划线 _"""
    if key is None:
        return None
    if isinstance(key, str):
        return key.replace("-", "_")
    return key


def convert_dict_hyphen_to_underscore(data: Any) -> Any:
    """递归地将字典中的键名从连字符形式转换为下划线形式"""
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
