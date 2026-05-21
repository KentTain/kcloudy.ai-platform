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
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.tree import TreeMixin
from framework.database.types.uuid import StringUUID

__all__ = [
    "Base",
    "BaseModel",
    "EngineManager",
    "get_engine",
    "get_session",
    "setup_engine",
    "async_session",
    "create_session",
    "AuditMixin",
    "TenantMixin",
    "TreeMixin",
    "StringUUID",
]
