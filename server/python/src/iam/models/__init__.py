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
from .audit_log import AuditLog
from .organization import Organization, UserOrganization
from .enums import (
    NotificationType,
    OrganizationStatus,
    OAuthProvider,
    PermissionRequestStatus,
    PermissionRequestType,
    PolicyEffect,
    PolicyType,
    RoleCode,
    TenantStatus,
    UserStatus,
)
from .menu import Menu, MenuPermission
from .notification import Notification, NotificationRead
from .oauth_connection import OAuthConnection
from .permission import Permission, RolePermission, UserRole
from .permission_request import PermissionCacheEvent, PermissionRequest
from .policy import Policy
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
    "OrganizationStatus",
    "TenantStatus",  # 保留，用于 IAM 模块验证租户状态
    "NotificationType",
    "PermissionRequestType",
    "PermissionRequestStatus",
    "PolicyType",
    "PolicyEffect",
    # 用户相关
    "User",
    "OAuthConnection",
    "UserTenant",  # 用户-租户关联，保留在 IAM 模块
    # 组织架构
    "Organization",
    "UserOrganization",
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
    # 审计日志
    "AuditLog",
    # 站内信
    "Notification",
    "NotificationRead",
    # 权限申请
    "PermissionRequest",
    "PermissionCacheEvent",
    # 企业策略
    "Policy",
]
