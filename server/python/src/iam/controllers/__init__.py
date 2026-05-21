"""
IAM 控制器模块
"""

from fastapi import APIRouter

from controllers.iam.auth_controller import router as auth_router
from controllers.iam.department_controller import router as department_router
from controllers.iam.oauth_controller import router as oauth_router
from controllers.iam.permission_controller import router as permission_router
from controllers.iam.role_controller import router as role_router
from controllers.iam.user_controller import router as user_router

# 创建 IAM 主路由
router = APIRouter(prefix="/iam", tags=["IAM"])

# 注册子路由
router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(user_router, prefix="/user", tags=["用户"])
router.include_router(role_router, prefix="/role", tags=["角色"])
router.include_router(permission_router, prefix="/permission", tags=["权限"])
router.include_router(department_router, prefix="/department", tags=["部门"])
router.include_router(oauth_router, prefix="/oauth", tags=["OAuth"])

__all__ = ["router"]
