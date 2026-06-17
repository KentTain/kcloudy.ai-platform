"""加密组件初始化"""

from ai.components.encryption.exceptions import (
    DecryptionError,
    EncryptionAlgorithmError,
    EncryptionConfigError,
    EncryptionError,
    EncryptionKeyError,
)
from ai.components.encryption.helpers import (
    generate_aes_key,
    generate_encryption_config_template,
    generate_rsa_key_pair,
)
from ai.components.encryption.impl.aes import AESEncryption, RSAEncryption
from ai.components.encryption.interfaces import BaseEncryption

__all__ = [
    # 异常类
    "EncryptionError",
    "EncryptionConfigError",
    "EncryptionAlgorithmError",
    "EncryptionKeyError",
    "DecryptionError",
    # 基类
    "BaseEncryption",
    # 实现类
    "AESEncryption",
    "RSAEncryption",
    # 辅助函数
    "generate_aes_key",
    "generate_rsa_key_pair",
    "generate_encryption_config_template",
]
