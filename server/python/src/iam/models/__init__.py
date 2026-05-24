"""
IAM 模块数据模型

包含身份与访问管理相关的所有模型。
"""

from .department import Department, UserDepartment
from .enums import (
    DepartmentStatus,
    OAuthProvider,
    RoleCode,
    TenantStatus,
    UserStatus,
)
from .oauth_connection import OAuthConnection
from .permission import Permission, RolePermission, UserRole
from .role import Role
from .system_setting import SystemSetting
from .system_setting_attribute import SystemSettingAttribute
from .tenant import Tenant
from .tenant_admin import TenantAdmin
from .tenant_config import TenantConfig
from .user import User
from .user_tenant import UserTenant

__all__ = [
    # 枚举
    "UserStatus",
    "OAuthProvider",
    "RoleCode",
    "DepartmentStatus",
    "TenantStatus",
    # 租户相关
    "Tenant",
    "TenantConfig",
    "TenantAdmin",
    "UserTenant",
    # 用户相关
    "User",
    "OAuthConnection",
    # 组织架构
    "Department",
    "UserDepartment",
    # RBAC
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    # 系统设置
    "SystemSetting",
    "SystemSettingAttribute",
]
