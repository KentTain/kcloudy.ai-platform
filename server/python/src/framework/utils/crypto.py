"""
加密工具模块

提供密码哈希、验证和强度校验功能。
使用 BCrypt 算法进行密码哈希。
提供 AES-256-GCM 加密功能，用于保护敏感配置信息。
"""

import os
import re
import secrets

import bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# BCrypt cost factor，值越大越安全但越慢
BCRYPT_COST_FACTOR = 12

# AES-GCM 配置
NONCE_LENGTH = 12  # GCM 推荐 12 字节


class CryptoError(Exception):
    """加密相关错误"""
    pass


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


# =============================================================================
# AES-256-GCM 加密（用于敏感配置信息）
# =============================================================================


def _get_master_key() -> bytes:
    """
    获取主密钥

    优先级：
    1. 环境变量 TENANT_ENCRYPTION_MASTER_KEY
    2. 自动生成（仅适用于开发环境）

    Returns:
        bytes: 32 字节的主密钥

    Raises:
        CryptoError: 生产环境未配置主密钥
    """
    # 从环境变量获取
    key_hex = os.environ.get("TENANT_ENCRYPTION_MASTER_KEY")
    if key_hex:
        try:
            key = bytes.fromhex(key_hex)
            if len(key) != 32:
                raise CryptoError("主密钥长度必须为 32 字节（64 个十六进制字符）")
            return key
        except ValueError as e:
            raise CryptoError(f"主密钥格式错误: {e}") from e

    # 检查是否为开发环境
    env = os.environ.get("PYTHON_SERVICE_ENV", "local")
    if env in ("local", "dev", "development"):
        # 开发环境自动生成
        key = secrets.token_bytes(32)
        # 打印到日志（仅开发环境）
        import warnings
        warnings.warn(
            f"[DEV ONLY] 自动生成加密主密钥。"
            f"设置环境变量 TENANT_ENCRYPTION_MASTER_KEY={key.hex()} 以持久化。",
            UserWarning
        )
        return key

    raise CryptoError(
        "未配置加密主密钥。请设置环境变量 TENANT_ENCRYPTION_MASTER_KEY "
        "（32 字节的十六进制字符串，共 64 个字符）"
    )


# 主密钥缓存
_master_key: bytes | None = None


def get_master_key() -> bytes:
    """
    获取主密钥（带缓存）

    Returns:
        bytes: 32 字节的主密钥
    """
    global _master_key
    if _master_key is None:
        _master_key = _get_master_key()
    return _master_key


def generate_tenant_key() -> str:
    """
    生成租户加密密钥

    Returns:
        str: 64 个十六进制字符（32 字节）
    """
    return secrets.token_hex(32)


def encrypt(plaintext: str, key: bytes | None = None) -> str:
    """
    使用 AES-256-GCM 加密

    Args:
        plaintext: 明文
        key: 加密密钥（默认使用主密钥）

    Returns:
        str: 加密后的数据（格式：nonce:ciphertext，均为十六进制）

    Raises:
        CryptoError: 加密失败
    """
    if not plaintext:
        return ""

    try:
        # 获取密钥
        if key is None:
            key = get_master_key()

        # 生成随机 nonce
        nonce = secrets.token_bytes(NONCE_LENGTH)

        # 加密
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

        # 返回格式：nonce:ciphertext
        return f"{nonce.hex()}:{ciphertext.hex()}"

    except Exception as e:
        raise CryptoError(f"加密失败: {e}") from e


def decrypt(encrypted: str, key: bytes | None = None) -> str:
    """
    使用 AES-256-GCM 解密

    Args:
        encrypted: 加密数据（格式：nonce:ciphertext）
        key: 解密密钥（默认使用主密钥）

    Returns:
        str: 解密后的明文

    Raises:
        CryptoError: 解密失败
    """
    if not encrypted:
        return ""

    try:
        # 解析格式
        parts = encrypted.split(":")
        if len(parts) != 2:
            raise CryptoError("无效的加密数据格式")

        nonce = bytes.fromhex(parts[0])
        ciphertext = bytes.fromhex(parts[1])

        # 获取密钥
        if key is None:
            key = get_master_key()

        # 解密
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext.decode("utf-8")

    except CryptoError:
        raise
    except Exception as e:
        raise CryptoError(f"解密失败: {e}") from e


def encrypt_with_tenant_key(plaintext: str, tenant_key: str) -> str:
    """
    使用租户密钥加密

    Args:
        plaintext: 明文
        tenant_key: 租户密钥（64 个十六进制字符）

    Returns:
        str: 加密后的数据
    """
    key = bytes.fromhex(tenant_key)
    return encrypt(plaintext, key)


def decrypt_with_tenant_key(encrypted: str, tenant_key: str) -> str:
    """
    使用租户密钥解密

    Args:
        encrypted: 加密数据
        tenant_key: 租户密钥（64 个十六进制字符）

    Returns:
        str: 解密后的明文
    """
    key = bytes.fromhex(tenant_key)
    return decrypt(encrypted, key)
