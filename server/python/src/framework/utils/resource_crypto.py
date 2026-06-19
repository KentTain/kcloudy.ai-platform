"""
资源配置密码加密工具

为资源配置（数据库、存储、缓存、队列、发布订阅）提供密码加密、解密和脱敏功能。
复用 framework.utils.crypto 的 AES-256-GCM 加密能力。
"""

from framework.utils.crypto import decrypt, encrypt


def encrypt_password(plain: str) -> str:
    """
    加密密码

    使用 AES-256-GCM 加密密码字段。

    Args:
        plain: 明文密码

    Returns:
        str: 加密后的密码（格式：nonce:ciphertext）

    Raises:
        CryptoError: 加密失败
    """
    if not plain:
        return ""
    return encrypt(plain)


def decrypt_password(cipher: str) -> str:
    """
    解密密码

    使用 AES-256-GCM 解密密码字段。

    Args:
        cipher: 加密后的密码

    Returns:
        str: 解密后的明文密码

    Raises:
        CryptoError: 解密失败
    """
    if not cipher:
        return ""
    return decrypt(cipher)


def mask_password(cipher: str | None) -> str:
    """
    脱敏密码

    返回脱敏后的密码字符串，用于 API 响应。
    无论密码是否加密，都返回固定长度的星号。

    Args:
        cipher: 加密后的密码（可为 None）

    Returns:
        str: 脱敏后的密码 "******"
    """
    if not cipher:
        return ""
    return "******"


def is_encrypted(value: str) -> bool:
    """
    检查值是否已加密

    加密后的格式为 nonce:ciphertext（两个十六进制字符串用冒号分隔）。

    Args:
        value: 待检查的值

    Returns:
        bool: 是否为加密格式
    """
    if not value:
        return False
    parts = value.split(":")
    if len(parts) != 2:
        return False
    try:
        # nonce 应为 24 个十六进制字符（12 字节）
        # ciphertext 长度不固定
        bytes.fromhex(parts[0])
        bytes.fromhex(parts[1])
        return True
    except ValueError:
        return False
