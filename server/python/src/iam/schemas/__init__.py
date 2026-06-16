"""
IAM 模块 Pydantic Schemas
"""

from iam.schemas.admin.system_setting import (
    SystemSettingAttributeCreate,
    SystemSettingAttributeResponse,
    SystemSettingCreate,
    SystemSettingListResponse,
    SystemSettingResponse,
    SystemSettingUpdate,
)
from iam.schemas.console.system_setting import (
    ConsoleSystemSettingAttributeResponse,
    ConsoleSystemSettingListResponse,
    ConsoleSystemSettingResponse,
)
from iam.schemas.department import (
    DepartmentCreate,
    DepartmentTreeResponse,
    DepartmentUpdate,
    DepartmentUserResponse,
    DepartmentResponse,
    UserDepartmentRequest,
)
from iam.schemas.login import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
)
from iam.schemas.menu import (
    MenuListResponse,
    MenuTreeNode,
)
from iam.schemas.oauth import (
    OAuthAuthorizeResponse,
    OAuthBindRequest,
    OAuthCallbackRequest,
    OAuthCompleteProfileRequest,
)
from iam.schemas.permission import (
    PermissionGroupResponse,
    PermissionListResponse,
    PermissionResponse,
)
from iam.schemas.role import (
    RoleCreate,
    RoleListResponse,
    RolePermissionRequest,
    RoleUpdate,
    RoleResponse,
    RoleWithPermissionsResponse,
)
from iam.schemas.token import (
    TokenPayload,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from iam.schemas.user import (
    PasswordChangeRequest,
    PasswordResetCodeRequest,
    PasswordResetRequest,
    UserListResponse,
    UserRegisterRequest,
    UserUpdate,
    UserResponse,
)

__all__ = [
    # 登录
    "LoginRequest",
    "LoginResponse",
    "LogoutRequest",
    "LogoutResponse",
    # 菜单
    "MenuTreeNode",
    "MenuListResponse",
    # Token
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    "TokenPayload",
    # 用户
    "UserRegisterRequest",
    "UserUpdate",
    "PasswordChangeRequest",
    "PasswordResetCodeRequest",
    "PasswordResetRequest",
    "UserResponse",
    "UserListResponse",
    # 角色
    "RoleCreate",
    "RoleUpdate",
    "RolePermissionRequest",
    "RoleResponse",
    "RoleListResponse",
    "RoleWithPermissionsResponse",
    # 权限
    "PermissionResponse",
    "PermissionListResponse",
    "PermissionGroupResponse",
    # 部门
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "DepartmentTreeResponse",
    "UserDepartmentRequest",
    "DepartmentUserResponse",
    # OAuth
    "OAuthAuthorizeResponse",
    "OAuthCallbackRequest",
    "OAuthCompleteProfileRequest",
    "OAuthBindRequest",
    # 系统设置 - Admin
    "SystemSettingCreate",
    "SystemSettingUpdate",
    "SystemSettingResponse",
    "SystemSettingListResponse",
    "SystemSettingAttributeCreate",
    "SystemSettingAttributeResponse",
    # 系统设置 - Console
    "ConsoleSystemSettingResponse",
    "ConsoleSystemSettingListResponse",
    "ConsoleSystemSettingAttributeResponse",
]
