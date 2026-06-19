"""
加密器模块

适配 framework 的加密工具，提供与 Alon 兼容的接口
"""

from framework.utils.crypto import decrypt, encrypt


def encrypt_token(tenant_id: str, token: str) -> str:
    """
    加密令牌

    Args:
        tenant_id: 租户 ID（用于兼容性，实际加密使用 framework 的主密钥）
        token: 要加密的令牌

    Returns:
        加密后的令牌字符串
    """
    # 使用 framework 的 AES-256-GCM 加密
    return encrypt(token)


def decrypt_token(tenant_id: str, encrypted_token: str) -> str:
    """
    解密令牌

    Args:
        tenant_id: 租户 ID（用于兼容性）
        encrypted_token: 加密的令牌

    Returns:
        解密后的令牌
    """
    # 使用 framework 的 AES-256-GCM 解密
    return decrypt(encrypted_token)


def obfuscated_token(token: str) -> str:
    """
    混淆令牌（用于显示）

    Args:
        token: 原始令牌

    Returns:
        混淆后的令牌
    """
    if not token or len(token) < 8:
        return "****"

    # 显示前 4 位和后 4 位，中间用 * 代替
    return token[:4] + "*" * (len(token) - 8) + token[-4:]


def get_decrypt_decoding(tenant_id: str) -> tuple:
    """
    获取解密密钥和加密器

    Args:
        tenant_id: 租户 ID

    Returns:
        解密密钥和加密器的元组
    """
    # 返回兼容性占位符
    return (None, None)


def decrypt_token_with_decoding(
    encrypted_token: str,
    decoding_key,
    cipher,
) -> str:
    """
    使用指定的解密密钥解密令牌

    Args:
        encrypted_token: 加密的令牌
        decoding_key: 解密密钥
        cipher: 加密器

    Returns:
        解密后的令牌
    """
    # 使用 framework 的解密
    return decrypt(encrypted_token)
