"""
加密工具模块

提供密码哈希、验证和强度校验功能。
使用 BCrypt 算法进行密码哈希。
"""

import re

import bcrypt

# BCrypt cost factor，值越大越安全但越慢
BCRYPT_COST_FACTOR = 12


def hash_password(password: str) -> str:
    """
    使用 BCrypt 对密码进行哈希。

    Args:
        password: 明文密码

    Returns:
        BCrypt 哈希值（60 字符）

    Raises:
        ValueError: 密码为空
    """
    if not password:
        raise ValueError("密码不能为空")

    salt = bcrypt.gensalt(rounds=BCRYPT_COST_FACTOR)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hash_value: str) -> bool:
    """
    验证密码是否匹配哈希值。

    Args:
        password: 明文密码
        hash_value: BCrypt 哈希值

    Returns:
        密码匹配返回 True，否则返回 False
    """
    if not password or not hash_value:
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hash_value.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def validate_password_strength(password: str) -> bool:
    """
    验证密码强度。

    要求：
    - 长度 8-32 位
    - 包含字母
    - 包含数字

    Args:
        password: 明文密码

    Returns:
        验证通过返回 True

    Raises:
        ValueError: 密码不符合强度要求
    """
    if not password:
        raise ValueError("密码不能为空")

    if len(password) < 8 or len(password) > 32:
        raise ValueError("密码长度需 8-32 位")

    has_letter = bool(re.search(r"[a-zA-Z]", password))
    has_digit = bool(re.search(r"\d", password))

    if not (has_letter and has_digit):
        raise ValueError("密码必须包含字母和数字")

    return True
