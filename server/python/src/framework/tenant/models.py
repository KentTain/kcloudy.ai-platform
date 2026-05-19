"""
租户模型定义

仅包含模型设计，不涉及具体实现。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from framework.tenant.enums import DatabaseType, StorageType, QueueType, PubSubType


@dataclass
class TenantDatabaseConfig:
    """租户数据库配置"""
    type: DatabaseType = DatabaseType.POSTGRESQL
    host: str = ""
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""


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
class Tenant:
    """
    租户模型

    包含租户的基本信息和资源配置。
    采用数据库级隔离策略。
    """

    id: str
    """租户 ID"""

    name: str
    """租户名称"""

    code: str
    """租户编码"""

    status: str = "active"
    """状态"""

    # 资源配置
    database: TenantDatabaseConfig = field(default_factory=TenantDatabaseConfig)
    """数据库配置"""

    storage: TenantStorageConfig = field(default_factory=TenantStorageConfig)
    """存储配置"""

    queue: TenantQueueConfig = field(default_factory=TenantQueueConfig)
    """队列配置"""

    pubsub: TenantPubSubConfig = field(default_factory=TenantPubSubConfig)
    """发布订阅配置"""

    # 联系人信息
    contact_name: str = ""
    """联系人姓名"""

    contact_email: str = ""
    """联系人邮箱"""

    contact_phone: str = ""
    """联系人电话"""

    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    """创建时间"""

    updated_at: datetime = field(default_factory=datetime.now)
    """更新时间"""

    expired_at: Optional[datetime] = None
    """过期时间"""

    # 扩展设置
    settings: dict[str, Any] = field(default_factory=dict)
    """扩展设置"""


@dataclass
class TenantSetting:
    """
    租户设置

    支持租户自定义配置。
    """

    tenant_id: str
    """租户 ID"""

    name: str
    """设置名称"""

    value: str
    """设置值"""

    description: str = ""
    """描述"""

    created_at: datetime = field(default_factory=datetime.now)
    """创建时间"""

    updated_at: datetime = field(default_factory=datetime.now)
    """更新时间"""
