"""
字典工具函数
"""

from typing import Any, TypeVar

T = TypeVar("T")


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    深度合并两个字典

    Args:
        base: 基础字典
        override: 覆盖字典

    Returns:
        dict: 合并后的字典
    """
    result = base.copy()

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def keys_to_snake_case(data: Any) -> Any:
    """
    递归将字典键名转换为下划线命名

    Args:
        data: 要处理的数据

    Returns:
        处理后的数据
    """
    from framework.utils.string_util import to_snake_case

    if data is None:
        return None

    if isinstance(data, dict):
        return {
            to_snake_case(k): keys_to_snake_case(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [keys_to_snake_case(item) for item in data]

    return data


def keys_to_camel_case(data: Any, capitalize_first: bool = False) -> Any:
    """
    递归将字典键名转换为驼峰命名

    Args:
        data: 要处理的数据
        capitalize_first: 是否大写首字母

    Returns:
        处理后的数据
    """
    from framework.utils.string_util import to_camel_case

    if data is None:
        return None

    if isinstance(data, dict):
        return {
            to_camel_case(k, capitalize_first): keys_to_camel_case(v, capitalize_first)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [keys_to_camel_case(item, capitalize_first) for item in data]

    return data


def get_nested_value(data: dict[str, Any], path: str, default: Any = None) -> Any:
    """
    获取嵌套字典中的值

    Args:
        data: 字典数据
        path: 路径，用点号分隔，如 "user.profile.name"
        default: 默认值

    Returns:
        值或默认值
    """
    if not path:
        return default

    keys = path.split(".")
    current = data

    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]

    return current


def set_nested_value(data: dict[str, Any], path: str, value: Any) -> None:
    """
    设置嵌套字典中的值

    Args:
        data: 字典数据
        path: 路径，用点号分隔
        value: 要设置的值
    """
    keys = path.split(".")
    current = data

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


def flatten_dict(
    data: dict[str, Any],
    parent_key: str = "",
    separator: str = "."
) -> dict[str, Any]:
    """
    扁平化嵌套字典

    Args:
        data: 嵌套字典
        parent_key: 父键前缀
        separator: 分隔符

    Returns:
        扁平化后的字典
    """
    items: list[tuple[str, Any]] = []

    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key

        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))

    return dict(items)


def unflatten_dict(
    data: dict[str, Any],
    separator: str = "."
) -> dict[str, Any]:
    """
    将扁平化字典还原为嵌套字典

    Args:
        data: 扁平化字典
        separator: 分隔符

    Returns:
        嵌套字典
    """
    result: dict[str, Any] = {}

    for key, value in data.items():
        keys = key.split(separator)
        current = result

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    return result
