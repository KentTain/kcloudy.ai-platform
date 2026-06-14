"""
用户菜单控制器

提供用户菜单查询接口。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse

from framework.common.ctx import get_tenant_id
from iam.dependencies import get_current_user_id
from iam.schemas.user_menu import UserMenuVo
from iam.services.user_menu_service import user_menu_service

router = APIRouter()


@router.get("/menus")
async def get_user_menus(
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    获取当前用户菜单树

    返回当前用户有权限访问的菜单树。

    场景：已登录用户获取菜单
    WHEN 已登录用户请求菜单列表
    THEN 系统返回该用户有权限查看的菜单树

    场景：用户无任何菜单权限
    WHEN 用户没有任何菜单权限
    THEN 系统返回空数组

    场景：未登录用户
    WHEN 未登录用户请求菜单列表
    THEN 系统返回 401 错误

    Returns:
        ORJSONResponse: 菜单树响应
    """
    tenant_id = get_tenant_id()
    menus = await user_menu_service.get_user_menus(user_id, tenant_id)

    # 转换为 UserMenuVo 格式
    def to_vo(menu_dict: dict) -> UserMenuVo:
        return UserMenuVo(
            id=menu_dict["id"],
            code=menu_dict["code"],
            name=menu_dict["name"],
            icon=menu_dict["icon"],
            path=menu_dict["path"],
            sort_order=menu_dict["sort_order"],
            children=[to_vo(child) for child in menu_dict["children"]],
        )

    data = [to_vo(m) for m in menus]

    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "获取成功",
            "data": [d.model_dump() for d in data],
        }
    )
