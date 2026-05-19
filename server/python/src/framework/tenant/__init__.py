"""
租户模块

提供多租户模型设计（仅模型，不含实现）。
"""

from framework.tenant.models import Tenant, TenantSetting
from framework.tenant.enums import DatabaseType, StorageType, QueueType
from framework.tenant.context import TenantContext, get_current_tenant, set_current_tenant

__all__ = [
    "Tenant",
    "TenantSetting",
    "DatabaseType",
    "StorageType",
    "QueueType",
    "TenantContext",
    "get_current_tenant",
    "set_current_tenant",
]
