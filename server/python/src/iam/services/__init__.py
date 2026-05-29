"""
IAM 服务模块
"""

from iam.services.auth_service import AuthService, auth_service
from iam.services.department_service import DepartmentService, department_service
from iam.services.menu_service import MenuService, menu_service
from iam.services.oauth_service import OAuthService, oauth_service
from iam.services.permission_service import (
    PermissionCheckService,
    PermissionService,
    permission_check_service,
    permission_service,
)
from iam.services.role_service import (
    RoleService,
    UserRoleService,
    role_service,
    user_role_service,
)
from iam.services.user_service import UserService, user_service

__all__ = [
    # 认证
    "AuthService",
    "auth_service",
    # 用户管理
    "UserService",
    "user_service",
    # 角色管理
    "RoleService",
    "role_service",
    "UserRoleService",
    "user_role_service",
    # 权限管理
    "PermissionService",
    "permission_service",
    "PermissionCheckService",
    "permission_check_service",
    # 部门管理
    "DepartmentService",
    "department_service",
    # 菜单管理
    "MenuService",
    "menu_service",
    # OAuth
    "OAuthService",
    "oauth_service",
]
