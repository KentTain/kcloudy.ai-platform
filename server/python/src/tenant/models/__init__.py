"""
Tenant 模块数据模型

包含租户管理相关的所有模型。
所有模型归属于 tenant PostgreSQL schema。
"""

from framework.database import create_module_base, create_base_model

# 创建 Tenant 模块的 Base 和 BaseModel
Base = create_module_base("tenant")
BaseModel = create_base_model(Base)

# 导入模型（必须在 Base 和 BaseModel 定义之后）
from .enums import TenantStatus
from .tenant import Tenant
from .tenant_admin import TenantAdmin
from .tenant_config import TenantConfig

__all__ = [
    "Base",
    "BaseModel",
    # 枚举
    "TenantStatus",
    # 租户相关
    "Tenant",
    "TenantConfig",
    "TenantAdmin",
]
