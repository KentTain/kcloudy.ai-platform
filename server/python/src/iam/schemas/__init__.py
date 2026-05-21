"""
IAM 模块 Pydantic Schemas
"""

from schemas.iam.department import (
    DepartmentCreateRequest,
    DepartmentTreeVo,
    DepartmentUpdateRequest,
    DepartmentUserVo,
    DepartmentVo,
    UserDepartmentRequest,
)
from schemas.iam.login import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
)
from schemas.iam.oauth import (
    OAuthAuthorizeResponse,
    OAuthBindRequest,
    OAuthCallbackRequest,
    OAuthCompleteProfileRequest,
)
from schemas.iam.permission import (
    PermissionGroupVo,
    PermissionListVo,
    PermissionVo,
)
from schemas.iam.role import (
    RoleCreateRequest,
    RoleListVo,
    RolePermissionRequest,
    RoleUpdateRequest,
    RoleVo,
    RoleWithPermissionsVo,
)
from schemas.iam.token import (
    TokenPayload,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from schemas.iam.user import (
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
]
