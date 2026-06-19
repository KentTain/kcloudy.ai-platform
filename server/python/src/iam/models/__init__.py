"""
IAM 模块数据模型

包含身份与访问管理相关的所有模型。
所有模型归属于 iam PostgreSQL schema。

注意：Tenant、TenantConfig、TenantAdmin 已迁移到 tenant 模块
"""

from framework.database import create_base_model, create_module_base

# 创建 IAM 模块的 Base 和 BaseModel
Base = create_module_base("iam")
BaseModel = create_base_model(Base)

# 导入模型（必须在 Base 和 BaseModel 定义之后）
from .department import Department, UserDepartment
from .enums import (
    DepartmentStatus,
    OAuthProvider,
    RoleCode,
    TenantStatus,
    UserStatus,
)
from .menu import Menu, MenuPermission
from .oauth_connection import OAuthConnection
from .permission import Permission, RolePermission, UserRole
from .role import Role
from .system_setting import SystemSetting
from .system_setting_attribute import SystemSettingAttribute
from .user import User
from .user_tenant import UserTenant

__all__ = [
    # Base
    "Base",
    "BaseModel",
    # 枚举
    "UserStatus",
    "OAuthProvider",
    "RoleCode",
    "DepartmentStatus",
    "TenantStatus",  # 保留，用于 IAM 模块验证租户状态
    # 用户相关
    "User",
    "OAuthConnection",
    "UserTenant",  # 用户-租户关联，保留在 IAM 模块
    # 组织架构
    "Department",
    "UserDepartment",
    # RBAC
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    # 菜单
    "Menu",
    "MenuPermission",
    # 系统设置
    "SystemSetting",
    "SystemSettingAttribute",
]
