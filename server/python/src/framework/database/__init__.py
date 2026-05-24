"""
数据库模块

提供 Base、Mixins、Types、Tree、Interceptors、Events 等组件。
"""

from framework.database.core.base import Base, BaseModel
from framework.database.core.engine import (
    EngineManager,
    get_engine,
    get_session,
    setup_engine,
    async_session,
    create_session,
)
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.property import (
    AttributeDataType,
    PropertyAttributeMixin,
    PropertyMixin,
)
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.mixins.tree import TreeMixin, TreeNodeMixin, TreeNodeEventType
from framework.database.mixins.uuid_primary_key import UUIDPrimaryKeyMixin
from framework.database.types.uuid import StringUUID

__all__ = [
    # Base
    "Base",
    "BaseModel",
    # Engine
    "EngineManager",
    "get_engine",
    "get_session",
    "setup_engine",
    "async_session",
    "create_session",
    # Mixins
    "ActiveRecordMixin",
    "AuditMixin",
    "PropertyMixin",
    "PropertyAttributeMixin",
    "TenantMixin",
    "TimestampMixin",
    "TreeMixin",
    "TreeNodeMixin",
    "UUIDPrimaryKeyMixin",
    # Types
    "StringUUID",
    # Enums
    "AttributeDataType",
    "TreeNodeEventType",
]
