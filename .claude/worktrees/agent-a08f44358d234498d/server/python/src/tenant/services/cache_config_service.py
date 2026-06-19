"""
缓存配置服务

提供缓存配置的 CRUD 操作和连通性测试。
"""

import time

from loguru import logger

from framework.utils.resource_crypto import decrypt_password
from tenant.models import CacheConfig
from tenant.services.base_resource_service import BaseResourceService

_logger = logger.bind(name=__name__)


class CacheConfigService(BaseResourceService):
    """缓存配置服务"""

    model_class = CacheConfig
    encrypt_fields = ["password"]
    sensitive_fields = ["password"]
    _reference_field = "cache_config_id"

    @classmethod
    async def test_connection(cls, config_id: str) -> tuple[bool, str, int | None]:
        """
        测试缓存连通性

        执行 PING 命令，超时 5 秒。

        Args:
            config_id: 配置 ID

        Returns:
            tuple[bool, str, int | None]: 成功/失败、消息、延迟（毫秒）
        """
        config = await cls.get_by_id(config_id)
        if not config:
            return False, "配置不存在", None

        start_time = time.monotonic()
        try:
            import redis.asyncio as redis

            # 解密密码
            password = (
                decrypt_password(config.password) if config.password else None
            )

            client = redis.Redis(
                host=config.host,
                port=config.port,
                password=password,
                db=config.db,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            result = await client.ping()
            await client.aclose()

            latency = int((time.monotonic() - start_time) * 1000)
            if result:
                _logger.info(
                    f"缓存连通性测试成功: {config.name}, 延迟: {latency}ms"
                )
                return True, f"连接成功，延迟 {latency}ms", latency
            else:
                return False, "PING 返回失败", latency

        except ImportError:
            # redis 未安装
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.warning(f"redis 未安装，跳过缓存连通性测试: {config.name}")
            return True, "检查通过（redis 未安装，仅做配置格式校验）", latency

        except Exception as e:
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.error(f"缓存连通性测试失败: {config.name}, 错误: {e}")
            return False, f"连接失败: {str(e)}", latency


# 服务单例
cache_config_service = CacheConfigService()
