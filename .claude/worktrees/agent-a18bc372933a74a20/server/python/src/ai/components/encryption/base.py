"""加密算法工厂"""

from ai.components.encryption.exceptions import (
    EncryptionAlgorithmError,
    EncryptionKeyError,
)
from ai.components.encryption.impl.aes import AESEncryption, RSAEncryption
from ai.components.encryption.interfaces import BaseEncryption


def create_encryption(algorithm: str, **kwargs) -> BaseEncryption:
    """
    创建加密算法实例

    Args:
        algorithm: 算法类型（aes, rsa）
        **kwargs: 算法参数

    Returns:
        加密算法实例
    """
    algorithm = algorithm.lower()

    if algorithm == "aes":
        key = kwargs.get("key")
        if not key:
            raise EncryptionKeyError("AES算法需要key参数")
        return AESEncryption(key)

    elif algorithm == "rsa":
        private_key = kwargs.get("pri_key")
        public_key = kwargs.get("pub_key")
        if not private_key and not public_key:
            raise EncryptionKeyError("RSA算法需要pri_key或pub_key参数")
        return RSAEncryption(private_key, public_key)

    else:
        raise EncryptionAlgorithmError(f"不支持的加密算法: {algorithm}")
