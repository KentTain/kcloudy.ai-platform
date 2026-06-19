"""加密管理器"""

from loguru import logger

from ai.components.encryption.base import create_encryption
from ai.components.encryption.exceptions import EncryptionConfigError, EncryptionError
from ai.components.encryption.interfaces import BaseEncryption
from framework.configs.encryption import (
    EncryptionInstanceSettings,
    EncryptionSettings,
)

_logger = logger.bind(name=__name__)


class EncryptionManager:
    """加密管理器"""

    def __init__(self, config: EncryptionSettings | None = None):
        """
        初始化加密管理器

        Args:
            config: 加密配置
        """
        self._instances: dict[str, BaseEncryption] = {}
        self._config = config

        if config and config.enabled:
            self._initialize_instances()

    def _initialize_instances(self):
        """初始化加密实例"""
        if not self._config or not self._config.instance:
            return

        for instance_config in self._config.instance:
            try:
                self._create_instance(instance_config)
            except Exception as e:
                _logger.exception(f"创建加密实例失败 {instance_config.name}")
                raise EncryptionConfigError(
                    f"创建加密实例失败 {instance_config.name}: {str(e)}"
                )

    def _create_instance(self, config: EncryptionInstanceSettings):
        """
        创建加密实例

        Args:
            config: 实例配置
        """
        kwargs = {}

        if config.algorithm.lower() == "aes":
            if not config.key:
                raise EncryptionConfigError(f"AES算法实例 {config.name} 缺少key配置")
            kwargs["key"] = config.key

        elif config.algorithm.lower() == "rsa":
            if not config.pri_key and not config.pub_key:
                raise EncryptionConfigError(
                    f"RSA算法实例 {config.name} 缺少pri_key或pub_key配置"
                )
            if config.pri_key:
                kwargs["pri_key"] = config.pri_key
            if config.pub_key:
                kwargs["pub_key"] = config.pub_key

        else:
            raise EncryptionConfigError(f"不支持的加密算法: {config.algorithm}")

        # 创建加密实例
        encryption = create_encryption(config.algorithm, **kwargs)
        self._instances[config.name] = encryption

        _logger.info(f"创建加密实例成功: {config.name} ({config.algorithm})")

    def get_instance(self, name: str) -> BaseEncryption:
        """
        获取加密实例

        Args:
            name: 实例名称

        Returns:
            加密实例

        Raises:
            EncryptionError: 实例不存在
        """
        if name not in self._instances:
            raise EncryptionError(f"加密实例不存在: {name}")

        return self._instances[name]

    def encrypt(self, name: str, data: str) -> str:
        """
        使用指定实例加密数据

        Args:
            name: 实例名称
            data: 要加密的数据

        Returns:
            加密后的数据
        """
        instance = self.get_instance(name)
        return instance.encrypt(data)

    def decrypt(self, name: str, encrypted_data: str) -> str:
        """
        使用指定实例解密数据

        Args:
            name: 实例名称
            encrypted_data: 要解密的数据

        Returns:
            解密后的数据
        """
        instance = self.get_instance(name)
        return instance.decrypt(encrypted_data)

    def has_instance(self, name: str) -> bool:
        """
        检查实例是否存在

        Args:
            name: 实例名称

        Returns:
            是否存在
        """
        return name in self._instances

    def list_instances(self) -> list[str]:
        """
        获取所有实例名称

        Returns:
            实例名称列表
        """
        return list(self._instances.keys())

    def is_enabled(self) -> bool:
        """
        检查加密是否启用

        Returns:
            是否启用
        """
        return self._config is not None and self._config.enabled

    def add_instance(self, name: str, algorithm: str, **kwargs):
        """
        动态添加加密实例

        Args:
            name: 实例名称
            algorithm: 算法类型
            **kwargs: 算法参数
        """
        if name in self._instances:
            raise EncryptionError(f"加密实例已存在: {name}")

        encryption = create_encryption(algorithm, **kwargs)
        self._instances[name] = encryption

        _logger.info(f"动态添加加密实例: {name} ({algorithm})")

    def remove_instance(self, name: str):
        """
        移除加密实例

        Args:
            name: 实例名称
        """
        if name not in self._instances:
            raise EncryptionError(f"加密实例不存在: {name}")

        del self._instances[name]
        _logger.info(f"移除加密实例: {name}")


# 全局加密管理器实例
_encryption_manager: EncryptionManager | None = None


def init_encryption_manager(
    config: EncryptionSettings | None = None,
) -> EncryptionManager:
    """
    初始化全局加密管理器

    Args:
        config: 加密配置

    Returns:
        加密管理器实例
    """
    global _encryption_manager
    _encryption_manager = EncryptionManager(config)
    return _encryption_manager


def get_encryption_manager() -> EncryptionManager:
    """
    获取全局加密管理器

    Returns:
        加密管理器实例

    Raises:
        EncryptionError: 管理器未初始化
    """
    if _encryption_manager is None:
        raise EncryptionError("加密管理器未初始化，请先调用 init_encryption_manager")

    return _encryption_manager
