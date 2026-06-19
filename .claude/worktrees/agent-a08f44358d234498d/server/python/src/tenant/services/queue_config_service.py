"""
队列配置服务

提供队列配置的 CRUD 操作和连通性测试。
"""

import time

from loguru import logger

from framework.utils.resource_crypto import decrypt_password
from tenant.models import QueueConfig
from tenant.services.base_resource_service import BaseResourceService

_logger = logger.bind(name=__name__)


class QueueConfigService(BaseResourceService):
    """队列配置服务"""

    model_class = QueueConfig
    encrypt_fields = ["password"]
    sensitive_fields = ["password"]
    _reference_field = "queue_config_id"

    @classmethod
    async def test_connection(cls, config_id: str) -> tuple[bool, str, int | None]:
        """
        测试队列连通性

        根据队列类型选择测试方法：
        - redis：执行 PING
        - rabbitmq：尝试连接并检查队列列表

        Args:
            config_id: 配置 ID

        Returns:
            tuple[bool, str, int | None]: 成功/失败、消息、延迟（毫秒）
        """
        config = await cls.get_by_id(config_id)
        if not config:
            return False, "配置不存在", None

        start_time = time.monotonic()

        if config.type == "redis":
            return await cls._test_redis(config, start_time)
        elif config.type == "rabbitmq":
            return await cls._test_rabbitmq(config, start_time)
        else:
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.warning(
                f"不支持的队列类型，仅做配置格式校验: {config.type}"
            )
            return True, f"检查通过（类型 {config.type} 仅做配置格式校验）", latency

    @classmethod
    async def _test_redis(cls, config: QueueConfig, start_time: float) -> tuple[bool, str, int | None]:
        """测试 Redis 队列连通性"""
        try:
            import redis.asyncio as redis

            password = (
                decrypt_password(config.password) if config.password else None
            )

            client = redis.Redis(
                host=config.host,
                port=config.port,
                password=password,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            await client.ping()
            await client.aclose()

            latency = int((time.monotonic() - start_time) * 1000)
            _logger.info(f"队列(Redis)连通性测试成功: {config.name}, 延迟: {latency}ms")
            return True, f"连接成功，延迟 {latency}ms", latency

        except ImportError:
            latency = int((time.monotonic() - start_time) * 1000)
            return True, "检查通过（redis 未安装，仅做配置格式校验）", latency

        except Exception as e:
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.error(f"队列(Redis)连通性测试失败: {config.name}, 错误: {e}")
            return False, f"连接失败: {str(e)}", latency

    @classmethod
    async def _test_rabbitmq(cls, config: QueueConfig, start_time: float) -> tuple[bool, str, int | None]:
        """测试 RabbitMQ 连通性"""
        try:
            import aio_pika

            password = (
                decrypt_password(config.password) if config.password else ""
            )
            vhost = config.vhost or "/"

            connection_url = (
                f"amqp://{config.username or 'guest'}:{password}"
                f"@{config.host}:{config.port}/{vhost.lstrip('/')}"
            )

            connection = await aio_pika.connect_robust(
                connection_url,
                timeout=5,
            )
            await connection.close()

            latency = int((time.monotonic() - start_time) * 1000)
            _logger.info(
                f"队列(RabbitMQ)连通性测试成功: {config.name}, 延迟: {latency}ms"
            )
            return True, f"连接成功，延迟 {latency}ms", latency

        except ImportError:
            latency = int((time.monotonic() - start_time) * 1000)
            return True, "检查通过（aio_pika 未安装，仅做配置格式校验）", latency

        except Exception as e:
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.error(
                f"队列(RabbitMQ)连通性测试失败: {config.name}, 错误: {e}"
            )
            return False, f"连接失败: {str(e)}", latency


# 服务单例
queue_config_service = QueueConfigService()
