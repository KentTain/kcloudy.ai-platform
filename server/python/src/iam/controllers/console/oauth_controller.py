"""
OAuth 控制器

提供第三方 OAuth2 登录接口。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.schemas.base import Success
from framework.utils.jwt import generate_access_token, generate_refresh_token
from iam.dependencies import get_current_user_id
from iam.schemas.oauth import OAuthCompleteProfileRequest
from iam.services import auth_service, oauth_service, user_service

router = APIRouter()


@router.get("/oauth/{provider}")
async def get_oauth_authorize(
    provider: str,
    redirect_uri: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取 OAuth 授权链接

    返回第三方 OAuth2 授权页面 URL。
    """
    try:
        result = await oauth_service.get_authorize_url(provider, redirect_uri)
        return Success(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    OAuth 回调处理

    处理第三方 OAuth2 回调，完成登录。
    """
    try:
        user, is_new = await oauth_service.handle_callback(
            session,
            provider=provider,
            code=code,
            state=state,
        )

        # 创建会话并生成 Token
        from framework.utils.session import create_session

        session_id = await create_session(
            user_id=user.id,
            tenant_id=None,
            ip=None,
        )

        payload = {
            "user_id": user.id,
            "session_id": session_id,
            "version": 1,
            "roles": [],
            "permissions": [],
        }

        jwt_secret = auth_service._get_jwt_secret()
        access_token = generate_access_token(payload, jwt_secret)
        refresh_token = generate_refresh_token(
            {"user_id": user.id, "session_id": session_id},
            jwt_secret,
        )

        return Success(
            data={
                "user_id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "need_complete_profile": not user.profile_completed,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": 7200,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/oauth/complete-profile")
async def complete_oauth_profile(
    data: OAuthCompleteProfileRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    OAuth 用户补全信息

    为 OAuth 登录用户设置密码和其他信息。
    """
    try:
        user = await user_service.complete_profile(
            session,
            user_id=user_id,
            password=data.password,
            email=data.email,
            phone=data.phone,
        )
        return Success(data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
