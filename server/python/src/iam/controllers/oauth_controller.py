"""
OAuth 控制器

提供第三方 OAuth2 登录接口。
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import ORJSONResponse, RedirectResponse

from schemas.iam.oauth import OAuthCompleteProfileRequest
from services.iam import auth_service, oauth_service, user_service

router = APIRouter()


@router.get("/{provider}")
async def get_oauth_authorize(provider: str, redirect_uri: str | None = None) -> ORJSONResponse:
    """
    获取 OAuth 授权链接

    返回第三方 OAuth2 授权页面 URL。
    """
    try:
        result = await oauth_service.get_authorize_url(provider, redirect_uri)
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "success",
                "data": result,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str) -> ORJSONResponse:
    """
    OAuth 回调处理

    处理第三方 OAuth2 回调，完成登录。
    """
    try:
        user, is_new = await oauth_service.handle_callback(
            provider=provider,
            code=code,
            state=state,
        )

        # 生成 Token
        # TODO: 调用 auth_service 生成 Token

        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "登录成功" if not is_new else "注册成功",
                "data": {
                    "user_id": user.id,
                    "username": user.username,
                    "nickname": user.nickname,
                    "need_complete_profile": not user.profile_completed,
                },
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/complete-profile")
async def complete_oauth_profile(request: Request, data: OAuthCompleteProfileRequest) -> ORJSONResponse:
    """
    OAuth 用户补全信息

    为 OAuth 登录用户设置密码和其他信息。
    """
    # TODO: 从请求中获取用户 ID
    user_id = "mock_user_id"

    try:
        user = await user_service.complete_profile(
            user_id=user_id,
            password=data.password,
            email=data.email,
            phone=data.phone,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "信息补全成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
