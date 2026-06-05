"""
IAM 依赖注入

提供认证相关的 FastAPI 依赖。
"""

from fastapi import Depends, HTTPException, Request

from framework.common.ctx import get_user_id, get_tenant_id, get_session_id


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
