"""加密辅助工具"""

import secrets
import string

from ai.components.encryption.impl.aes import AESEncryption, RSAEncryption


def generate_aes_key(length: int = 32) -> str:
    """
    生成AES密钥字符串

    Args:
        length: 密钥长度，默认32字节（256位）

    Returns:
        AES密钥字符串
    """
    # 生成包含字母、数字和特殊字符的随机密钥
    alphabet = string.ascii_letters + string.digits + "~!@#$%^&*()_+-="
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_rsa_key_pair(key_size: int = 2048) -> tuple[str, str]:
    """
    生成RSA密钥对字符串

    Args:
        key_size: 密钥长度，默认2048位

    Returns:
        (私钥字符串, 公钥字符串) 元组
    """
    return RSAEncryption.generate_key_pair(key_size)


def generate_encryption_config_template() -> dict:
    """
    生成加密配置模板

    Returns:
        加密配置字典模板
    """
    # 生成密钥
    aes_key = generate_aes_key()
    private_key, public_key = generate_rsa_key_pair()

    return {
        "encryption": {
            "enabled": True,
            "instance": [
                {"name": "db-in", "algorithm": "aes", "key": aes_key},
                {
                    "name": "web-in",
                    "algorithm": "rsa",
                    "pri-key": private_key,
                    "pub-key": public_key,
                },
            ],
            "db-in": {"enabled": True, "use": "db-in"},
            "web-in": {"enabled": True, "use": "web-in"},
            "web-out": {"temp-key-ttl": 300},
        },
    }
