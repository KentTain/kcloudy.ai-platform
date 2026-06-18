"""
租户实例层权限 API

提供租户权限列表的只读查询接口。
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from iam.models import Permission
from iam.schemas.permission import PermissionPaginatedQuery

router = APIRouter(prefix="/tenants/{tenant_id}", tags=["Tenant Permission"])


@router.get("/permissions")
async def get_tenant_permissions(
    tenant_id: str,
    query: PermissionPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    获取租户权限列表

    返回指定租户的所有权限。

    Args:
        tenant_id: 租户 ID
        query: 分页查询参数

    Returns:
        权限列表和总数
    """
    # 查询总数
    count_stmt = select(func.count(Permission.id)).where(
        Permission.tenant_id == tenant_id
    )
    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    # 查询列表
    offset = (query.page - 1) * query.page_size
    stmt = (
        select(Permission)
        .where(Permission.tenant_id == tenant_id)
        .order_by(Permission.created_at.desc())
        .offset(offset)
        .limit(query.page_size)
    )
    result = await session.execute(stmt)
    permissions = list(result.scalars().all())

    return {
        "items": [
            {
                "id": p.id,
                "tenant_id": p.tenant_id,
                "code": p.code,
                "name": p.name,
                "resource": p.resource,
                "action": p.action,
                "description": p.description,
                "ref_id": p.ref_id,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            for p in permissions
        ],
        "total": total,
        "page": query.page,
        "page_size": query.page_size,
    }


@router.get("/permissions/{permission_id}")
async def get_tenant_permission(
    tenant_id: str,
    permission_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    获取租户权限详情

    Args:
        tenant_id: 租户 ID
        permission_id: 权限 ID

    Returns:
        权限详情
    """
    stmt = select(Permission).where(
        Permission.tenant_id == tenant_id,
        Permission.id == permission_id,
    )
    result = await session.execute(stmt)
    permission = result.scalar_one_or_none()

    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")

    return {
        "id": permission.id,
        "tenant_id": permission.tenant_id,
        "code": permission.code,
        "name": permission.name,
        "resource": permission.resource,
        "action": permission.action,
        "description": permission.description,
        "ref_id": permission.ref_id,
        "created_at": permission.created_at,
        "updated_at": permission.updated_at,
    }
