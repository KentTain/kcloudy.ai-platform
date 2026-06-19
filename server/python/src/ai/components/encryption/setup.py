"""加密组件初始化"""

from loguru import logger

from ai.components.encryption.manager import (
    get_encryption_manager,
    init_encryption_manager,
)
from framework.configs.encryption import EncryptionSettings
from framework.configs.settings import get_settings

_logger = logger.bind(name=__name__)

# 全局状态
_encryption_initialized: bool = False
_encryption_config: EncryptionSettings | None = None


async def setup_encryption() -> None:
    """
    初始化加密组件

    从全局配置中读取配置。该函数完全独立工作，不依赖其他组件。
    """
    global _encryption_initialized, _encryption_config

    try:
        # 如果已经初始化，直接返回
        if _encryption_initialized:
            _logger.info("加密组件已经初始化")
            return

        # 从全局配置获取加密配置
        settings = get_settings()
        config: EncryptionSettings | None = settings.encryption

        if not config:
            _logger.info("未找到加密配置，使用默认配置")
            return

        _logger.info("开始初始化加密组件")

        # 初始化加密管理器
        init_encryption_manager(config)
        _logger.info("加密管理器初始化完成")

        # 验证初始化结果
        manager = get_encryption_manager()

        _logger.info(f"加密组件初始化成功，可用实例: {manager.list_instances()}")
        _encryption_initialized = True

    except Exception:
        _logger.exception("初始化加密组件时出错")
