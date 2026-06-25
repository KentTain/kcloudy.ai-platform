"""
IAM 依赖注入

提供认证相关的 FastAPI 依赖。
"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.ctx import get_session_id, get_tenant_id, get_user_id
from framework.database.dependencies import get_db_session


def get_current_user_id(request: Request) -> str:
    """
    从上下文中获取当前用户 ID

    Args:
        request: FastAPI 请求对象

    Returns:
        str: 用户 ID

    Raises:
        HTTPException: 未登录 (401)
    """
    user_id = get_user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")
    return user_id


def get_optional_user_id(request: Request) -> str | None:
    """
    从上下文中获取当前用户 ID（可选）

    Args:
        request: FastAPI 请求对象

    Returns:
        str | None: 用户 ID，未登录返回 None
    """
    return get_user_id()


def get_current_tenant_id(request: Request) -> str:
    """
    从上下文中获取当前租户 ID

    Args:
        request: FastAPI 请求对象

    Returns:
        str: 租户 ID

    Raises:
        HTTPException: 缺少租户上下文 (400)
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="缺少租户上下文")
    return tenant_id


def get_current_session_id(request: Request) -> str:
    """
    从上下文中获取当前会话 ID

    Args:
        request: FastAPI 请求对象

    Returns:
        str: 会话 ID

    Raises:
        HTTPException: 未登录 (401)
    """
    session_id = get_session_id()
    if not session_id:
        raise HTTPException(status_code=401, detail="未登录")
    return session_id


def require_permission(permission_code: str):
    """
    权限检查依赖工厂

    创建一个检查指定权限的 FastAPI 依赖。

    Args:
        permission_code: 需要的权限编码

    Returns:
        依赖函数

    Usage:
        @router.get("/users")
        async def list_users(
            _: None = Depends(require_permission("user:read")),
            session: AsyncSession = Depends(get_db_session),
        ):
            ...
    """

    async def check_permission(
        session: AsyncSession = Depends(get_db_session),
    ) -> None:
        from iam.services import permission_check_service

        user_id = get_user_id()
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        has_perm = await permission_check_service.has_permission(
            session, user_id, permission_code
        )
        if not has_perm:
            raise HTTPException(status_code=403, detail="权限不足")

    return check_permission


def require_any_permission(permission_codes: list[str]):
    """
    多选一权限检查依赖工厂

    创建一个检查任一权限的 FastAPI 依赖。

    Args:
        permission_codes: 权限编码列表，拥有任一即可

    Returns:
        依赖函数

    Usage:
        @router.get("/users")
        async def list_users(
            _: None = Depends(require_any_permission(["user:read", "user:list"])),
            session: AsyncSession = Depends(get_db_session),
        ):
            ...
    """

    async def check_permission(
        session: AsyncSession = Depends(get_db_session),
    ) -> None:
        from iam.services import permission_check_service

        user_id = get_user_id()
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        has_perm = await permission_check_service.has_any_permission(
            session, user_id, permission_codes
        )
        if not has_perm:
            raise HTTPException(status_code=403, detail="权限不足")

    return check_permission
