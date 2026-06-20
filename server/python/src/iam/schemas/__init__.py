"""
IAM 模块 Pydantic Schemas
"""

from iam.schemas.admin.system_setting import (
    SystemSettingAttributeCreate,
    SystemSettingAttributeResponse,
    SystemSettingCreate,
    SystemSettingPaginatedListResponse,
    SystemSettingPaginatedQuery,
    SystemSettingQuery,
    SystemSettingResponse,
    SystemSettingUpdate,
)
from iam.schemas.console.system_setting import (
    ConsoleSystemSettingAttributeResponse,
    ConsoleSystemSettingPaginatedListResponse,
    ConsoleSystemSettingPaginatedQuery,
    ConsoleSystemSettingQuery,
    ConsoleSystemSettingResponse,
)
from iam.schemas.organization import (
    MemberInfo,
    OrganizationCreate,
    OrganizationDetailResponse,
    OrganizationResponse,
    OrganizationTreeResponse,
    OrganizationUpdate,
    OrganizationUserBatchRequest,
    OrganizationUserResponse,
    UserOrganizationRequest,
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
    PermissionPaginatedQuery,
    PermissionQuery,
    PermissionResponse,
)
from iam.schemas.role import (
    RoleCreate,
    RoleMemberAssignRequest,
    RoleMemberResponse,
    RoleMenuAssignRequest,
    RoleOptionResponse,
    RolePaginatedListResponse,
    RolePaginatedQuery,
    RolePermissionRequest,
    RoleQuery,
    RoleResponse,
    RoleUpdate,
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
    UserPaginatedListResponse,
    UserPaginatedQuery,
    UserQuery,
    UserRegisterRequest,
    UserResponse,
    UserStatsResponse,
    UserUpdate,
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
    # 组织
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "OrganizationTreeResponse",
    "UserOrganizationRequest",
    "OrganizationUserResponse",
    "OrganizationUserBatchRequest",
    "OrganizationDetailResponse",
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
