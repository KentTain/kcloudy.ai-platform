"""
租户协议定义

提供租户信息的抽象接口，支持依赖倒置。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from framework.tenant.enums import DatabaseType, StorageType, QueueType, PubSubType


# ============== 资源配置 ==============


@dataclass
class TenantDatabaseConfig:
    """租户数据库配置"""

    type: DatabaseType = DatabaseType.POSTGRESQL
    host: str = ""
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""  # 已解密的密码


@dataclass
class TenantStorageConfig:
    """租户存储配置"""

    type: StorageType = StorageType.MINIO
    endpoint: str = ""
    access_key: str = ""
    secret_key: str = ""
    bucket: str = ""


@dataclass
class TenantQueueConfig:
    """租户队列配置"""

    type: QueueType = QueueType.REDIS
    endpoint: str = ""


@dataclass
class TenantPubSubConfig:
    """租户发布订阅配置"""

    type: PubSubType = PubSubType.REDIS
    endpoint: str = ""


@dataclass
class TenantCacheConfig:
    """租户缓存配置"""

    db: int = 0  # Redis DB 编号 (0-15)


# ============== TenantInfo Protocol ==============


class TenantInfo(Protocol):
    """
    租户信息协议

    用于上下文传递和服务间通信。
    包含基础信息和可选的资源配置，支持租户级资源隔离。
    """

    # ========== 基础信息 ==========
    @property
    def id(self) -> str:
        """租户 ID"""
        ...

    @property
    def name(self) -> str:
        """租户名称"""
        ...

    @property
    def code(self) -> str:
        """租户编码"""
        ...

    @property
    def status(self) -> str:
        """状态"""
        ...

    # ========== 时间信息（可选）==========
    @property
    def expired_at(self) -> datetime | None:
        """过期时间"""
        ...

    # ========== 联系人信息（可选）==========
    @property
    def contact_name(self) -> str | None:
        """联系人姓名"""
        ...

    @property
    def contact_email(self) -> str | None:
        """联系人邮箱"""
        ...

    @property
    def contact_phone(self) -> str | None:
        """联系人电话"""
        ...

    # ========== 资源配置（可选）==========
    @property
    def database(self) -> TenantDatabaseConfig | None:
        """数据库配置（租户级隔离）"""
        ...

    @property
    def storage(self) -> TenantStorageConfig | None:
        """存储配置（租户级隔离）"""
        ...

    @property
    def queue(self) -> TenantQueueConfig | None:
        """队列配置（租户级隔离）"""
        ...

    @property
    def pubsub(self) -> TenantPubSubConfig | None:
        """发布订阅配置（租户级隔离）"""
        ...

    @property
    def cache(self) -> TenantCacheConfig | None:
        """缓存配置（租户级隔离）"""
        ...


# ============== TenantProvider Protocol ==============


class TenantProvider(Protocol):
    """
    租户提供者协议

    抽象租户获取逻辑，支持：
    - 本地部署：直接数据库访问
    - 分布式部署：通过 RPC/HTTP 调用 IAM 服务
    """

    async def get_tenant(self, tenant_id: str) -> TenantInfo | None:
        """
        获取租户信息

        Args:
            tenant_id: 租户 ID

        Returns:
            TenantInfo | None
        """
        ...

    async def validate_access(self, user_id: str, tenant_id: str) -> bool:
        """
        验证用户是否有权访问租户

        Args:
            user_id: 用户 ID
            tenant_id: 租户 ID

        Returns:
            bool
        """
        ...

    async def get_user_tenants(self, user_id: str) -> list[TenantInfo]:
        """
        获取用户所属的租户列表

        Args:
            user_id: 用户 ID

        Returns:
            list[TenantInfo]
        """
        ...


# ============== 全局注册 ==============

_tenant_provider: TenantProvider | None = None


def register_tenant_provider(provider: TenantProvider) -> None:
    """
    注册租户提供者

    应用启动时调用，注入具体实现。

    Args:
        provider: TenantProvider 实现实例
    """
    global _tenant_provider
    _tenant_provider = provider


def get_tenant_provider() -> TenantProvider:
    """
    获取租户提供者

    Returns:
        TenantProvider 实例

    Raises:
        RuntimeError: 未注册时抛出
    """
    if _tenant_provider is None:
        raise RuntimeError(
            "TenantProvider not registered. "
            "Call register_tenant_provider() at startup."
        )
    return _tenant_provider
