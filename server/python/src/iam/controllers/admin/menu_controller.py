"""
菜单控制器

提供菜单查询接口。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse
from iam.schemas.menu import MenuListResponse, MenuTreeNode
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
    return ApiResponse.success(
        data=MenuListResponse(
            menus=[MenuTreeNode.model_validate(m) for m in menus]
        ).model_dump()
    )
