"""
数据库配置服务

提供数据库配置的 CRUD 操作和连通性测试。
"""

import time

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from framework.utils.resource_crypto import decrypt_password
from tenant.models import DatabaseConfig
from tenant.services.base_resource_service import BaseResourceService

_logger = logger.bind(name=__name__)


class DatabaseConfigService(BaseResourceService):
    """数据库配置服务"""

    model_class = DatabaseConfig
    encrypt_fields = ["password"]
    sensitive_fields = ["password"]
    _reference_field = "db_config_id"

    @classmethod
    async def test_connection(cls, config_id: str) -> tuple[bool, str, int | None]:
        """
        测试数据库连通性

        尝试建立连接并执行 SELECT 1，超时 5 秒。

        Args:
            config_id: 配置 ID

        Returns:
            tuple[bool, str, int | None]: 成功/失败、消息、延迟（毫秒）
        """
        config = await cls.get_by_id(config_id)
        if not config:
            return False, "配置不存在", None

        # 解密密码
        try:
            password = decrypt_password(config.password)
        except Exception as e:
            _logger.error(f"解密数据库密码失败: {e}")
            return False, "密码解密失败", None

        # 构建连接 URL
        driver = "postgresql+asyncpg"
        if config.type == "mysql":
            driver = "mysql+aiomysql"
        elif config.type == "sqlite":
            driver = "sqlite+aiosqlite"

        url = f"{driver}://{config.username}:{password}@{config.host}:{config.port}/{config.database}"

        start_time = time.monotonic()
        try:
            engine = create_async_engine(
                url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 5},
            )
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()

            latency = int((time.monotonic() - start_time) * 1000)
            _logger.info(f"数据库连通性测试成功: {config.name}, 延迟: {latency}ms")
            return True, f"连接成功，延迟 {latency}ms", latency

        except Exception as e:
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.error(f"数据库连通性测试失败: {config.name}, 错误: {e}")
            return False, f"连接失败: {str(e)}", latency


# 服务单例
database_config_service = DatabaseConfigService()
