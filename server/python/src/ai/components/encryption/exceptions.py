"""加密组件异常定义"""


class EncryptionError(Exception):
    """加密基础异常"""

    pass


class EncryptionConfigError(EncryptionError):
    """加密配置异常"""

    pass


class EncryptionAlgorithmError(EncryptionError):
    """加密算法异常"""

    pass


class EncryptionKeyError(EncryptionError):
    """加密密钥异常"""

    pass


class DecryptionError(EncryptionError):
    """解密异常"""

    pass
