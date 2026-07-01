"""
菜单控制器

提供菜单查询接口。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse
from iam.schemas.menu import MenuListResponse, MenuTreeNode
from iam.schemas.permission import PermissionResponse
from iam.services import menu_service

router = APIRouter()


@router.get("/menus")
async def get_all_menus(
    session: AsyncSession = Depends(get_db_session),
):
    """
    获取所有菜单（树形）

    场景：管理员配置角色权限
    """
    menus = await menu_service.get_all_menus(session)
    return ApiResponse.success(data={"menus": menus})


@router.get("/menus/{menu_id}/permissions")
async def get_menu_permissions(
    menu_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    获取菜单关联的权限列表

    场景：管理员配置菜单权限时查看已关联的权限
    """
    permissions = await menu_service.get_menu_permissions(session, menu_id)
    return ApiResponse.success(data=permissions)
