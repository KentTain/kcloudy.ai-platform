"""
IAM 控制器模块
"""

from fastapi import APIRouter

from iam.controllers.auth_controller import router as auth_router
from iam.controllers.department_controller import router as department_router
from iam.controllers.menu_controller import router as menu_router
from iam.controllers.oauth_controller import router as oauth_router
from iam.controllers.permission_controller import router as permission_router
from iam.controllers.role_controller import router as role_router
from iam.controllers.user_controller import router as user_router

# 创建 IAM 主路由
router = APIRouter(prefix="/iam", tags=["IAM"])

# 注册子路由
router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(user_router, prefix="/user", tags=["用户"])
router.include_router(role_router, prefix="/role", tags=["角色"])
router.include_router(permission_router, prefix="/permission", tags=["权限"])
router.include_router(department_router, prefix="/department", tags=["部门"])
router.include_router(oauth_router, prefix="/oauth", tags=["OAuth"])
router.include_router(menu_router, prefix="/menu", tags=["菜单"])

__all__ = ["router"]
