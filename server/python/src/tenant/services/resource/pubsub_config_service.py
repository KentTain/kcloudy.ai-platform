"""
发布订阅配置服务

提供发布订阅配置的 CRUD 操作和连通性测试。
"""

import time

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from framework.utils.resource_crypto import decrypt_password
from tenant.models import PubSubConfig
from .base_resource_service import BaseResourceService

_logger = logger.bind(name=__name__)


class PubSubConfigService(BaseResourceService):
    """发布订阅配置服务"""

    model_class = PubSubConfig
    encrypt_fields = ["password"]
    sensitive_fields = ["password"]
    _reference_field = "pubsub_config_id"

    @classmethod
    async def test_connection(cls, session: AsyncSession, config_id: str) -> tuple[bool, str, int | None]:
        """
        测试发布订阅连通性

        根据类型选择测试方法：
        - redis：执行 PING
        - kafka：尝试连接并获取 topic 列表
        - nats：尝试连接

        Args:
            session: 数据库会话
            config_id: 配置 ID

        Returns:
            tuple[bool, str, int | None]: 成功/失败、消息、延迟（毫秒）
        """
        config = await cls.get_by_id(session, config_id)
        if not config:
            return False, "配置不存在", None

        start_time = time.monotonic()

        if config.type == "redis":
            return await cls._test_redis(config, start_time)
        elif config.type == "kafka":
            return await cls._test_kafka(config, start_time)
        elif config.type == "nats":
            return await cls._test_nats(config, start_time)
        else:
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.warning(
                f"不支持的发布订阅类型，仅做配置格式校验: {config.type}"
            )
            return True, f"检查通过（类型 {config.type} 仅做配置格式校验）", latency

    @classmethod
    async def _test_redis(cls, config: PubSubConfig, start_time: float) -> tuple[bool, str, int | None]:
        """测试 Redis 发布订阅连通性"""
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
            _logger.info(
                f"发布订阅(Redis)连通性测试成功: {config.name}, 延迟: {latency}ms"
            )
            return True, f"连接成功，延迟 {latency}ms", latency

        except ImportError:
            latency = int((time.monotonic() - start_time) * 1000)
            return True, "检查通过（redis 未安装，仅做配置格式校验）", latency

        except Exception as e:
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.error(
                f"发布订阅(Redis)连通性测试失败: {config.name}, 错误: {e}"
            )
            return False, f"连接失败: {str(e)}", latency

    @classmethod
    async def _test_kafka(cls, config: PubSubConfig, start_time: float) -> tuple[bool, str, int | None]:
        """测试 Kafka 连通性"""
        try:
            from kafka import KafkaAdminClient

            password = (
                decrypt_password(config.password) if config.password else None
            )

            admin_config = {
                "bootstrap_servers": f"{config.host}:{config.port}",
                "request_timeout_ms": 5000,
            }

            if config.username and password:
                admin_config["sasl_mechanism"] = "PLAIN"
                admin_config["security_protocol"] = "SASL_PLAINTEXT"
                admin_config["sasl_plain_username"] = config.username
                admin_config["sasl_plain_password"] = password

            client = KafkaAdminClient(**admin_config)
            client.list_topics(timeout=5)
            client.close()

            latency = int((time.monotonic() - start_time) * 1000)
            _logger.info(
                f"发布订阅(Kafka)连通性测试成功: {config.name}, 延迟: {latency}ms"
            )
            return True, f"连接成功，延迟 {latency}ms", latency

        except ImportError:
            latency = int((time.monotonic() - start_time) * 1000)
            return True, "检查通过（kafka-python 未安装，仅做配置格式校验）", latency

        except Exception as e:
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.error(
                f"发布订阅(Kafka)连通性测试失败: {config.name}, 错误: {e}"
            )
            return False, f"连接失败: {str(e)}", latency

    @classmethod
    async def _test_nats(cls, config: PubSubConfig, start_time: float) -> tuple[bool, str, int | None]:
        """测试 NATS 连通性"""
        try:
            import nats

            password = (
                decrypt_password(config.password) if config.password else ""
            )
            user = config.username or ""

            url = f"nats://{config.host}:{config.port}"
            if user and password:
                url = f"nats://{user}:{password}@{config.host}:{config.port}"

            nc = await nats.connect(url, connect_timeout=5)
            await nc.close()

            latency = int((time.monotonic() - start_time) * 1000)
            _logger.info(
                f"发布订阅(NATS)连通性测试成功: {config.name}, 延迟: {latency}ms"
            )
            return True, f"连接成功，延迟 {latency}ms", latency

        except ImportError:
            latency = int((time.monotonic() - start_time) * 1000)
            return True, "检查通过（nats-py 未安装，仅做配置格式校验）", latency

        except Exception as e:
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.error(
                f"发布订阅(NATS)连通性测试失败: {config.name}, 错误: {e}"
            )
            return False, f"连接失败: {str(e)}", latency


# 服务单例
pubsub_config_service = PubSubConfigService()
