"""
部门树字段数据填充脚本

为现有部门数据填充 tree_leaf、tree_level、tree_sort、tree_sorts、tree_names、parent_ids 字段。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.core.constants import DEFAULT_SORT, TREE_SORTS_LENGTH, DEFAULT_TREE_ROOT_ID
from framework.database.dependencies import get_task_session
from iam.models import Department


async def seed_tree_fields():
    """填充部门树字段"""
    async with get_task_session() as session:
        # 查询所有部门
        stmt = select(Department).order_by(Department.sort_order)
        result = await session.execute(stmt)
        departments = result.scalars().all()

        # 构建 ID -> Department 映射
        dept_map = {d.id: d for d in departments}

        for dept in departments:
            # 计算 tree_level
            if not dept.parent_id or dept.parent_id == DEFAULT_TREE_ROOT_ID:
                dept.tree_level = 0
                dept.parent_ids = f"{DEFAULT_TREE_ROOT_ID},"
            else:
                parent = dept_map.get(dept.parent_id)
                if parent:
                    dept.tree_level = parent.tree_level + 1
                    dept.parent_ids = f"{parent.parent_ids}{parent.id},"
                else:
                    dept.tree_level = 1
                    dept.parent_ids = f"{DEFAULT_TREE_ROOT_ID},{dept.parent_id},"

            # 计算 tree_sort
            dept.tree_sort = dept.sort_order or DEFAULT_SORT

            # 计算 tree_sorts
            if not dept.parent_id or dept.parent_id == DEFAULT_TREE_ROOT_ID:
                dept.tree_sorts = str(dept.tree_sort).zfill(TREE_SORTS_LENGTH) + ","
            else:
                parent = dept_map.get(dept.parent_id)
                if parent:
                    dept.tree_sorts = f"{parent.tree_sorts}{str(dept.tree_sort).zfill(TREE_SORTS_LENGTH)},"
                else:
                    dept.tree_sorts = str(dept.tree_sort).zfill(TREE_SORTS_LENGTH) + ","

            # 计算 tree_names
            if not dept.parent_id or dept.parent_id == DEFAULT_TREE_ROOT_ID:
                dept.tree_names = dept.name
            else:
                parent = dept_map.get(dept.parent_id)
                if parent:
                    dept.tree_names = f"{parent.tree_names}/{dept.name}"
                else:
                    dept.tree_names = dept.name

            # 计算 tree_leaf
            has_children = any(d.parent_id == dept.id for d in departments)
            dept.tree_leaf = not has_children

            # 更新父节点的 tree_leaf 状态
            if dept.parent_id and dept.parent_id != DEFAULT_TREE_ROOT_ID:
                parent = dept_map.get(dept.parent_id)
                if parent:
                    parent.tree_leaf = False

        await session.commit()
        print(f"已填充 {len(departments)} 个部门的树字段")


if __name__ == "__main__":
    asyncio.run(seed_tree_fields())