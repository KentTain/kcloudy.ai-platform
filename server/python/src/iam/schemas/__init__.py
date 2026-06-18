"""
IAM 模块 Pydantic Schemas
"""

from iam.schemas.admin.system_setting import (
    SystemSettingAttributeCreate,
    SystemSettingAttributeResponse,
    SystemSettingCreate,
    SystemSettingPaginatedListResponse,
    SystemSettingResponse,
    SystemSettingUpdate,
    SystemSettingQuery,
    SystemSettingPaginatedQuery,
)
from iam.schemas.console.system_setting import (
    ConsoleSystemSettingAttributeResponse,
    ConsoleSystemSettingPaginatedListResponse,
    ConsoleSystemSettingResponse,
    ConsoleSystemSettingQuery,
    ConsoleSystemSettingPaginatedQuery,
)
from iam.schemas.department import (
    DepartmentCreate,
    DepartmentTreeResponse,
    DepartmentUpdate,
    DepartmentUserResponse,
    DepartmentResponse,
    UserDepartmentRequest,
    DepartmentUserBatchRequest,
    DepartmentDetailResponse,
    MemberInfo,
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
    PermissionPaginatedListResponse,
    PermissionResponse,
    PermissionQuery,
    PermissionPaginatedQuery,
)
from iam.schemas.role import (
    RoleCreate,
    RolePaginatedListResponse,
    RolePermissionRequest,
    RoleUpdate,
    RoleResponse,
    RoleWithPermissionsResponse,
    RoleOptionResponse,
    RoleMemberAssignRequest,
    RoleMenuAssignRequest,
    RoleMemberResponse,
    RoleQuery,
    RolePaginatedQuery,
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
    UserPaginatedListResponse,
    UserRegisterRequest,
    UserUpdate,
    UserResponse,
    UserQuery,
    UserPaginatedQuery,
    UserStatsResponse,
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
    "UserQuery",
    "UserPaginatedQuery",
    "UserPaginatedListResponse",
    "UserStatsResponse",
    # 角色
    "RoleCreate",
    "RoleUpdate",
    "RolePermissionRequest",
    "RoleResponse",
    "RoleQuery",
    "RolePaginatedQuery",
    "RolePaginatedListResponse",
    "RoleWithPermissionsResponse",
    "RoleOptionResponse",
    "RoleMemberAssignRequest",
    "RoleMenuAssignRequest",
    "RoleMemberResponse",
    # 权限
    "PermissionResponse",
    "PermissionQuery",
    "PermissionPaginatedQuery",
    "PermissionPaginatedListResponse",
    "PermissionGroupResponse",
    # 部门
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "DepartmentTreeResponse",
    "UserDepartmentRequest",
    "DepartmentUserResponse",
    "DepartmentUserBatchRequest",
    "DepartmentDetailResponse",
    "MemberInfo",
    # OAuth
    "OAuthAuthorizeResponse",
    "OAuthCallbackRequest",
    "OAuthCompleteProfileRequest",
    "OAuthBindRequest",
    # 系统设置 - Admin
    "SystemSettingCreate",
    "SystemSettingUpdate",
    "SystemSettingResponse",
    "SystemSettingQuery",
    "SystemSettingPaginatedQuery",
    "SystemSettingPaginatedListResponse",
    "SystemSettingAttributeCreate",
    "SystemSettingAttributeResponse",
    # 系统设置 - Console
    "ConsoleSystemSettingResponse",
    "ConsoleSystemSettingQuery",
    "ConsoleSystemSettingPaginatedQuery",
    "ConsoleSystemSettingPaginatedListResponse",
    "ConsoleSystemSettingAttributeResponse",
]
