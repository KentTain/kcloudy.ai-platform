"""
菜单控制器

提供菜单查询接口。
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import ORJSONResponse

from iam.schemas.menu import MenuListResponse, MenuTreeNode
from iam.services import menu_service

router = APIRouter()


def _get_current_user_id(request: Request) -> str | None:
    """
    从请求中获取当前用户 ID

    TODO: 替换为统一的认证依赖注入（如 Depends(get_current_user)）
    """
    return request.state.user_id if hasattr(request.state, "user_id") else None


@router.get("/user")
async def get_user_menus(request: Request) -> ORJSONResponse:
    """
    获取当前用户可见菜单树

    场景：已登录用户获取菜单
    WHEN 已登录用户请求菜单列表
    THEN 系统返回该用户有权限查看的菜单树

    场景：未登录用户请求菜单
    WHEN 未登录用户请求菜单列表
    THEN 系统返回 401 未授权错误

    场景：用户无任何菜单权限
    WHEN 用户没有任何菜单权限
    THEN 系统返回空数组

    场景：菜单无权限限制
    WHEN 菜单未关联任何权限
    THEN 所有登录用户可见此菜单（is_visible = true 时）
    """
    user_id = _get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")

    menus = await menu_service.get_user_menus(user_id)

    # 使用 ORJSONResponse 保持与其他 IAM 控制器响应格式一致
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": MenuListResponse(
                menus=[MenuTreeNode.model_validate(m) for m in menus]
            ).model_dump(),
        }
    )
