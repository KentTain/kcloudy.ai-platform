"""
组织树字段数据填充脚本

为现有组织数据填充 tree_leaf、tree_level、tree_sort、tree_sorts、tree_names、parent_ids 字段。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from sqlalchemy import select

from framework.core.constants import (
    DEFAULT_SORT,
    DEFAULT_TREE_ROOT_ID,
    TREE_SORTS_LENGTH,
)
from framework.database.dependencies import get_task_session
from iam.models import Organization


async def seed_tree_fields():
    """填充组织树字段"""
    async with get_task_session() as session:
        # 查询所有组织
        stmt = select(Organization).order_by(Organization.sort_order)
        result = await session.execute(stmt)
        organizations = result.scalars().all()

        # 构建 ID -> Organization 映射
        org_map = {d.id: d for d in organizations}

        for org in organizations:
            # 计算 tree_level
            if not org.parent_id or org.parent_id == DEFAULT_TREE_ROOT_ID:
                org.tree_level = 0
                org.parent_ids = f"{DEFAULT_TREE_ROOT_ID},"
            else:
                parent = org_map.get(org.parent_id)
                if parent:
                    org.tree_level = parent.tree_level + 1
                    org.parent_ids = f"{parent.parent_ids}{parent.id},"
                else:
                    org.tree_level = 1
                    org.parent_ids = f"{DEFAULT_TREE_ROOT_ID},{org.parent_id},"

            # 计算 tree_sort
            org.tree_sort = org.sort_order or DEFAULT_SORT

            # 计算 tree_sorts
            if not org.parent_id or org.parent_id == DEFAULT_TREE_ROOT_ID:
                org.tree_sorts = str(org.tree_sort).zfill(TREE_SORTS_LENGTH) + ","
            else:
                parent = org_map.get(org.parent_id)
                if parent:
                    org.tree_sorts = f"{parent.tree_sorts}{str(org.tree_sort).zfill(TREE_SORTS_LENGTH)},"
                else:
                    org.tree_sorts = str(org.tree_sort).zfill(TREE_SORTS_LENGTH) + ","

            # 计算 tree_names
            if not org.parent_id or org.parent_id == DEFAULT_TREE_ROOT_ID:
                org.tree_names = org.name
            else:
                parent = org_map.get(org.parent_id)
                if parent:
                    org.tree_names = f"{parent.tree_names}/{org.name}"
                else:
                    org.tree_names = org.name

            # 计算 tree_leaf
            has_children = any(d.parent_id == org.id for d in organizations)
            org.tree_leaf = not has_children

            # 更新父节点的 tree_leaf 状态
            if org.parent_id and org.parent_id != DEFAULT_TREE_ROOT_ID:
                parent = org_map.get(org.parent_id)
                if parent:
                    parent.tree_leaf = False

        await session.commit()
        print(f"已填充 {len(organizations)} 个组织的树字段")


if __name__ == "__main__":
    asyncio.run(seed_tree_fields())
