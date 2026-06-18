"""
租户实例层角色 API

提供租户角色列表和角色权限的只读查询接口。
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from iam.models import Role, Permission, RolePermission
from iam.schemas.role import RolePaginatedQuery

router = APIRouter(prefix="/tenants/{tenant_id}", tags=["Tenant Role"])


@router.get("/roles")
async def get_tenant_roles(
    tenant_id: str,
    query: RolePaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    获取租户角色列表

    返回指定租户的所有角色。

    Args:
        tenant_id: 租户 ID
        query: 分页查询参数

    Returns:
        角色列表和总数
    """
    # 查询总数
    count_stmt = select(func.count(Role.id)).where(
        Role.tenant_id == tenant_id
    )
    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    # 查询列表
    offset = (query.page - 1) * query.page_size
    stmt = (
        select(Role)
        .where(Role.tenant_id == tenant_id)
        .order_by(Role.created_at.desc())
        .offset(offset)
        .limit(query.page_size)
    )
    result = await session.execute(stmt)
    roles = list(result.scalars().all())

    return {
        "items": [
            {
                "id": r.id,
                "tenant_id": r.tenant_id,
                "code": r.code,
                "name": r.name,
                "description": r.description,
                "is_system": r.is_system,
                "ref_id": r.ref_id,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in roles
        ],
        "total": total,
        "page": query.page,
        "page_size": query.page_size,
    }


@router.get("/roles/{role_id}")
async def get_tenant_role(
    tenant_id: str,
    role_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    获取租户角色详情（含权限列表）

    Args:
        tenant_id: 租户 ID
        role_id: 角色 ID

    Returns:
        角色详情（含权限列表）
    """
    # 查询角色
    stmt = select(Role).where(
        Role.tenant_id == tenant_id,
        Role.id == role_id,
    )
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 查询角色的权限列表
    perm_stmt = (
        select(Permission)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .where(
            RolePermission.tenant_id == tenant_id,
            RolePermission.role_id == role_id,
        )
    )
    perm_result = await session.execute(perm_stmt)
    permissions = list(perm_result.scalars().all())

    return {
        "id": role.id,
        "tenant_id": role.tenant_id,
        "code": role.code,
        "name": role.name,
        "description": role.description,
        "is_system": role.is_system,
        "ref_id": role.ref_id,
        "created_at": role.created_at,
        "updated_at": role.updated_at,
        "permissions": [
            {
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "resource": p.resource,
                "action": p.action,
                "description": p.description,
            }
            for p in permissions
        ],
    }
