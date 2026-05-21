"""
用户控制器

提供用户注册、信息管理、密码管理等接口。
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import ORJSONResponse

from schemas.iam.user import (
    PasswordChangeRequest,
    PasswordResetCodeRequest,
    PasswordResetRequest,
    UserRegisterRequest,
    UserUpdateRequest,
    UserVo,
)
from services.iam import auth_service, user_service

router = APIRouter()


def _get_current_user_id(request: Request) -> str | None:
    """从请求中获取当前用户 ID"""
    # TODO: 从认证中间件获取
    return request.state.user_id if hasattr(request.state, "user_id") else None


@router.post("/register")
async def register(data: UserRegisterRequest) -> ORJSONResponse:
    """
    用户注册

    创建新用户账号并自动登录。
    """
    try:
        user = await user_service.register(
            username=data.username,
            password=data.password,
            email=data.email,
            phone=data.phone,
        )

        # 自动登录
        # TODO: 生成 Token

        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "注册成功",
                "data": UserVo.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
async def get_current_user(request: Request) -> ORJSONResponse:
    """
    获取当前用户信息

    返回当前登录用户的详细信息。
    """
    user_id = _get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")

    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": UserVo.model_validate(user).model_dump(),
        }
    )


@router.put("/me")
async def update_current_user(request: Request, data: UserUpdateRequest) -> ORJSONResponse:
    """
    修改当前用户信息

    更新昵称、头像、邮箱、手机号等。
    """
    user_id = _get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")

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
                "data": UserVo.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/password")
async def change_password(request: Request, data: PasswordChangeRequest) -> ORJSONResponse:
    """
    修改密码

    验证原密码后设置新密码。
    """
    user_id = _get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")

    try:
        await user_service.change_password(
            user_id=user_id,
            old_password=data.old_password,
            new_password=data.new_password,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "密码修改成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/password/reset-code")
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


@router.post("/password/reset")
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
