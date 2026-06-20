"""
认证控制器

提供登录、登出、Token 刷新等接口。
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse
from iam.schemas.login import LoginRequest
from iam.schemas.token import TokenRefreshRequest
from iam.services import auth_service

router = APIRouter()


@router.post("/auth/login")
async def login(
    request: Request,
    data: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    用户登录

    支持用户名、邮箱、手机号三种登录方式。
    """
    try:
        ip = request.client.host if request.client else None
        result = await auth_service.login(
            session,
            account=data.account,
            password=data.password,
            ip=ip,
        )
        return ApiResponse.success(data=result.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/logout")
async def logout(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    用户登出

    将 Token 加入黑名单，使会话失效。
    """
    # 从请求头获取 Token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
        await auth_service.logout(access_token)

    return ApiResponse.success(data=None)


@router.post("/auth/token/refresh")
async def refresh_token(
    data: TokenRefreshRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    刷新 Token

    使用 Refresh Token 获取新的 Access Token。
    """
    try:
        result = await auth_service.refresh_token(data.refresh_token)
        return ApiResponse.success(data=result.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
