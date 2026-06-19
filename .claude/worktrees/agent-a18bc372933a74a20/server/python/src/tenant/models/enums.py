"""
Tenant 模块枚举定义
"""

from enum import Enum


class TenantStatus(str, Enum):
    """租户状态常量"""

    ACTIVE = "active"
    INACTIVE = "inactive"
