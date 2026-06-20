"""
全局角色种子数据初始化

创建全局共享角色 sysAdmin 和 normalUser。
全局角色的 module_id 为 NULL，表示不属于任何特定模块。
权限通过通配符匹配（fnmatch）在同步时展开为具体权限。
"""

from __future__ import annotations

from sqlalchemy import select

from framework.module.definition import GLOBAL_ROLES
from framework.utils.log_util import write_info, write_success, write_warning
from tenant.models import ModuleRole


async def run(*, dry_run: bool = False) -> int:
    """初始化全局角色数据

    创建全局共享角色（sysAdmin、normalUser），如果已存在则跳过。
    全局角色的权限关联由 ModuleDefinitionSyncService 在模块定义同步时处理。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.database.core.engine import get_session

    created_count = 0

    async with get_session() as session:
        for role_def in GLOBAL_ROLES:
            # 检查是否已存在（通过 code 匹配，module_id 为 NULL）
            result = await session.execute(
                select(ModuleRole).where(
                    ModuleRole.module_id.is_(None),
                    ModuleRole.code == role_def.code,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                write_info(f"全局角色已存在: {role_def.code} ({role_def.name})，跳过创建")
                continue

            if dry_run:
                write_info(f"[DRY-RUN] 将创建全局角色: {role_def.code} ({role_def.name})")
                created_count += 1
                continue

            role = ModuleRole(
                module_id=None,
                code=role_def.code,
                name=role_def.name,
                description=role_def.description,
                is_system=role_def.is_system,
            )
            session.add(role)
            await session.flush()
            created_count += 1
            write_success(f"已创建全局角色: {role_def.code} ({role_def.name})")

        if not dry_run:
            await session.commit()

        if created_count:
            write_success(f"已创建 {created_count} 个全局角色")
        else:
            write_warning("全局角色已初始化，无需变更")

        return created_count
