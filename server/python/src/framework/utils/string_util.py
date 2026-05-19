"""
字符串工具函数
"""

import re
from typing import Any


def to_snake_case(text: str) -> str:
    """
    将驼峰命名转换为下划线命名

    Args:
        text: 驼峰命名字符串

    Returns:
        str: 下划线命名字符串

    Example:
        >>> to_snake_case("UserName")
        'user_name'
    """
    if not text:
        return text

    result = text

    # 在小写字母和大写字母之间插入下划线（如 userName -> user_Name）
    result = re.sub(r"([a-z])([A-Z])", r"\1_\2", result)

    # 在连续大写字母和后续的大写字母+小写字母之间插入下划线（如 XMLParser -> XML_Parser）
    result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", result)

    # 转换为小写
    return result.lower()


def to_camel_case(text: str, capitalize_first: bool = False) -> str:
    """
    将下划线命名转换为驼峰命名

    Args:
        text: 下划线命名字符串
        capitalize_first: 是否大写首字母（Pascal 风格）

    Returns:
        str: 驼峰命名字符串

    Example:
        >>> to_camel_case("user_name")
        'userName'
        >>> to_camel_case("user_name", capitalize_first=True)
        'UserName'
    """
    if not text:
        return text

    components = text.split("_")
    if capitalize_first:
        return "".join(x.title() for x in components)
    else:
        return components[0] + "".join(x.title() for x in components[1:])


def mask_string(
    text: str,
    start: int = 0,
    end: int = 0,
    mask_char: str = "*"
) -> str:
    """
    字符串掩码处理

    Args:
        text: 原始字符串
        start: 保留的前几个字符
        end: 保留的后几个字符
        mask_char: 掩码字符

    Returns:
        str: 掩码后的字符串

    Example:
        >>> mask_string("13812345678", start=3, end=4)
        '138****5678'
    """
    if not text:
        return text

    length = len(text)

    if start + end >= length:
        return text

    masked_length = length - start - end
    return text[:start] + mask_char * masked_length + text[-end:] if end > 0 else text[:start] + mask_char * masked_length


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        str: 截断后的字符串
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def is_empty(value: Any) -> bool:
    """
    检查值是否为空（None 或空字符串）

    Args:
        value: 要检查的值

    Returns:
        bool: 是否为空
    """
    return value is None or (isinstance(value, str) and value.strip() == "")


def is_not_empty(value: Any) -> bool:
    """
    检查值是否不为空

    Args:
        value: 要检查的值

    Returns:
        bool: 是否不为空
    """
    return not is_empty(value)
