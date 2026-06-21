"""
数据库模型混入
"""

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.property import PropertyMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.mixins.tree import TreeNodeMixin
from framework.database.mixins.uuid_primary_key import UUIDPrimaryKeyMixin

__all__ = [
    "ActiveRecordMixin",
    "AuditMixin",
    "PropertyMixin",
    "TenantMixin",
    "TimestampMixin",
    "TreeNodeMixin",
    "UUIDPrimaryKeyMixin",
]
