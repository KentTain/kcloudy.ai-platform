"""
IAM 模块 Pydantic Schemas
"""

from iam.schemas.admin.system_setting import (
    SystemSettingAttributeCreate,
    SystemSettingAttributeResponse,
    SystemSettingCreate,
    SystemSettingListVo,
    SystemSettingResponse,
    SystemSettingUpdate,
)
from iam.schemas.console.system_setting import (
    ConsoleSystemSettingAttributeResponse,
    ConsoleSystemSettingListVo,
    ConsoleSystemSettingResponse,
)
from iam.schemas.department import (
    DepartmentCreateRequest,
    DepartmentTreeVo,
    DepartmentUpdateRequest,
    DepartmentUserVo,
    DepartmentVo,
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
    PermissionGroupVo,
    PermissionListVo,
    PermissionVo,
)
from iam.schemas.role import (
    RoleCreateRequest,
    RoleListVo,
    RolePermissionRequest,
    RoleUpdateRequest,
    RoleVo,
    RoleWithPermissionsVo,
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
    UserListVo,
    UserRegisterRequest,
    UserUpdateRequest,
    UserVo,
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
    "UserUpdateRequest",
    "PasswordChangeRequest",
    "PasswordResetCodeRequest",
    "PasswordResetRequest",
    "UserVo",
    "UserListVo",
    # 角色
    "RoleCreateRequest",
    "RoleUpdateRequest",
    "RolePermissionRequest",
    "RoleVo",
    "RoleListVo",
    "RoleWithPermissionsVo",
    # 权限
    "PermissionVo",
    "PermissionListVo",
    "PermissionGroupVo",
    # 部门
    "DepartmentCreateRequest",
    "DepartmentUpdateRequest",
    "DepartmentVo",
    "DepartmentTreeVo",
    "UserDepartmentRequest",
    "DepartmentUserVo",
    # OAuth
    "OAuthAuthorizeResponse",
    "OAuthCallbackRequest",
    "OAuthCompleteProfileRequest",
    "OAuthBindRequest",
    # 系统设置 - Admin
    "SystemSettingCreate",
    "SystemSettingUpdate",
    "SystemSettingResponse",
    "SystemSettingListVo",
    "SystemSettingAttributeCreate",
    "SystemSettingAttributeResponse",
    # 系统设置 - Console
    "ConsoleSystemSettingResponse",
    "ConsoleSystemSettingListVo",
    "ConsoleSystemSettingAttributeResponse",
]
