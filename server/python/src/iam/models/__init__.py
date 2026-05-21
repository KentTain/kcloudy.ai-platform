"""
IAM 模块数据模型

包含身份与访问管理相关的所有模型。
"""

from models.iam.department import Department, UserDepartment
from models.iam.enums import (
    DepartmentStatus,
    OAuthProvider,
    RoleCode,
    TenantStatus,
    UserStatus,
)
from models.iam.oauth_connection import OAuthConnection
from models.iam.permission import Permission, RolePermission, UserRole
from models.iam.role import Role
from models.iam.tenant import Tenant
from models.iam.tenant_admin import TenantAdmin
from models.iam.tenant_config import TenantConfig
from models.iam.user import User
from models.iam.user_tenant import UserTenant

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
]
