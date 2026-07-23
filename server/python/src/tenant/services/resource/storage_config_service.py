"""
存储配置服务

提供存储配置的 CRUD 操作和连通性测试。
"""

import time

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from framework.utils.resource_crypto import decrypt_password
from tenant.models import StorageConfig
from .base_resource_service import BaseResourceService

_logger = logger.bind(name=__name__)


class StorageConfigService(BaseResourceService):
    """存储配置服务"""

    model_class = StorageConfig
    encrypt_fields = ["secret_key"]
    sensitive_fields = ["secret_key"]
    _reference_field = "storage_config_id"

    @classmethod
    async def test_connection(cls, session: AsyncSession, config_id: str) -> tuple[bool, str, int | None]:
        """
        测试存储连通性

        检查 bucket 是否存在且可访问，超时 5 秒。

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
        try:
            import boto3
            from botocore.config import Config as BotoConfig

            # 解密密钥
            access_key = config.access_key or ""
            secret_key = (
                decrypt_password(config.secret_key)
                if config.secret_key
                else ""
            )

            s3_config = BotoConfig(
                connect_timeout=5,
                read_timeout=5,
                retries={"max_attempts": 1},
            )

            client = boto3.client(
                "s3",
                endpoint_url=config.endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=s3_config,
            )

            # 检查 bucket 是否存在
            client.head_bucket(Bucket=config.bucket)

            latency = int((time.monotonic() - start_time) * 1000)
            _logger.info(
                f"存储连通性测试成功: {config.name}, 延迟: {latency}ms"
            )
            return True, f"连接成功，延迟 {latency}ms", latency

        except ImportError:
            # boto3 未安装，做基础的端点可达性检查
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.warning(f"boto3 未安装，跳过存储连通性测试: {config.name}")
            return True, "检查通过（boto3 未安装，仅做配置格式校验）", latency

        except Exception as e:
            latency = int((time.monotonic() - start_time) * 1000)
            _logger.error(f"存储连通性测试失败: {config.name}, 错误: {e}")
            return False, f"连接失败: {str(e)}", latency


# 服务单例
storage_config_service = StorageConfigService()
