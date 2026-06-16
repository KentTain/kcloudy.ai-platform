"""
用户端用户控制器

提供用户注册、个人信息管理、密码管理、菜单查询等接口。
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import ORJSONResponse

from framework.tenant.context import get_tenant_id
from iam.dependencies import get_current_user_id
from iam.schemas.user import (
    PasswordChangeRequest,
    PasswordResetCodeRequest,
    PasswordResetRequest,
    UserRegisterRequest,
    UserUpdate,
    UserResponse,
)
from iam.schemas.user_menu import UserMenuTreeResponse
from iam.services import auth_service, user_service
from iam.services.user_menu_service import user_menu_service

router = APIRouter()


@router.post("/users/register")
async def register(data: UserRegisterRequest) -> ORJSONResponse:
    """
    用户注册

    创建新用户账号并自动登录。
    """
    # 从上下文获取租户 ID
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="缺少租户上下文")

    try:
        user = await user_service.register(
            username=data.username,
            password=data.password,
            tenant_id=tenant_id,
            email=data.email,
            phone=data.phone,
        )

        # 自动登录，生成 Token
        login_result = await auth_service.login(
            account=data.username,
            password=data.password,
        )

        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "注册成功",
                "data": {
                    "user": UserResponse.model_validate(user).model_dump(),
                    "access_token": login_result.access_token,
                    "refresh_token": login_result.refresh_token,
                    "expires_in": login_result.expires_in,
                },
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/me")
async def get_current_user(user_id: str = Depends(get_current_user_id)) -> ORJSONResponse:
    """
    获取当前用户信息

    返回当前登录用户的详细信息，包括角色、权限和租户列表。
    """
    user_detail = await user_service.get_user_detail(user_id)
    if not user_detail:
        raise HTTPException(status_code=404, detail="用户不存在")

    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": user_detail.model_dump(),
        }
    )


@router.put("/users/me")
async def update_current_user(
    data: UserUpdate,
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    修改当前用户信息

    更新昵称、头像、邮箱、手机号等。
    """
    try:
        user = await user_service.update_profile(
            user_id=user_id,
            nickname=data.nickname,
            avatar=data.avatar,
            email=data.email,
            phone=data.phone,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "修改成功",
                "data": UserResponse.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/password")
async def change_password(
    data: PasswordChangeRequest,
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    修改密码

    验证原密码后设置新密码。
    """
    try:
        await user_service.change_password(
            user_id=user_id,
            old_password=data.old_password,
            new_password=data.new_password,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "密码修改成功，请重新登录",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/password/reset-code")
async def send_reset_code(data: PasswordResetCodeRequest) -> ORJSONResponse:
    """
    发送密码重置验证码

    向邮箱或手机号发送 6 位验证码。
    """
    # TODO: 实现验证码发送
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "验证码已发送",
            "data": None,
        }
    )


@router.post("/users/password/reset")
async def reset_password(data: PasswordResetRequest) -> ORJSONResponse:
    """
    重置密码

    使用验证码重置密码。
    """
    try:
        await user_service.reset_password(
            email=data.email,
            phone=data.phone,
            code=data.code,
            new_password=data.new_password,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "密码重置成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/menus")
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

    # 转换为 UserMenuTreeResponse 格式
    def to_vo(menu_dict: dict) -> UserMenuTreeResponse:
        return UserMenuTreeResponse(
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
