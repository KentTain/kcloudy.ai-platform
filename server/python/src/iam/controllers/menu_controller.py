"""
菜单控制器

提供菜单查询接口。
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import ORJSONResponse

from iam.dependencies import get_current_user_id
from iam.schemas.menu import MenuListResponse, MenuTreeNode
from iam.services import menu_service

router = APIRouter()


@router.get("/user")
async def get_user_menus(user_id: str = Depends(get_current_user_id)) -> ORJSONResponse:
    """
    获取当前用户可见菜单树

    场景：已登录用户获取菜单
    """
    menus = await menu_service.get_user_menus(user_id)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": MenuListResponse(
                menus=[MenuTreeNode.model_validate(m) for m in menus]
            ).model_dump(),
        }
    )


@router.get("")
async def get_all_menus() -> ORJSONResponse:
    """
    获取所有菜单（树形）

    场景：管理员配置角色权限
    """
    menus = await menu_service.get_all_menus()
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": MenuListResponse(
                menus=[MenuTreeNode.model_validate(m) for m in menus]
            ).model_dump(),
        }
    )
