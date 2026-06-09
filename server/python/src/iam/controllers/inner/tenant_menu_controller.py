"""
租户实例层菜单 API

提供租户菜单树的只读查询接口。
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.core.engine import async_session
from iam.models import Menu, Role, Permission, RolePermission

router = APIRouter(prefix="/tenants/{tenant_id}", tags=["Tenant Menu"])


@router.get("/menus", response_model=list[dict[str, Any]])
async def get_tenant_menus(tenant_id: str) -> list[dict[str, Any]]:
    """
    获取租户菜单树

    返回指定租户的所有菜单，按树形结构组织。

    Args:
        tenant_id: 租户 ID

    Returns:
        菜单树列表
    """
    async with async_session() as session:
        # 查询租户所有菜单
        stmt = (
            select(Menu)
            .where(Menu.tenant_id == tenant_id)
            .order_by(Menu.tree_sorts)
        )
        result = await session.execute(stmt)
        menus = list(result.scalars().all())

        if not menus:
            return []

        # 构建菜单树
        return Menu.build_tree(menus)


@router.get("/menus/{menu_id}", response_model=dict[str, Any])
async def get_tenant_menu(tenant_id: str, menu_id: str) -> dict[str, Any]:
    """
    获取租户菜单详情

    Args:
        tenant_id: 租户 ID
        menu_id: 菜单 ID

    Returns:
        菜单详情
    """
    async with async_session() as session:
        stmt = select(Menu).where(
            Menu.tenant_id == tenant_id,
            Menu.id == menu_id,
        )
        result = await session.execute(stmt)
        menu = result.scalar_one_or_none()

        if not menu:
            raise HTTPException(status_code=404, detail="菜单不存在")

        return {
            "id": menu.id,
            "tenant_id": menu.tenant_id,
            "parent_id": menu.parent_id,
            "module": menu.module,
            "code": menu.code,
            "name": menu.name,
            "path": menu.path,
            "icon": menu.icon,
            "is_visible": menu.is_visible,
            "ref_id": menu.ref_id,
            "created_at": menu.created_at,
            "updated_at": menu.updated_at,
        }
