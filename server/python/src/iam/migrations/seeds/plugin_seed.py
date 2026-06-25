"""
插件管理权限数据权限数据初始化

初始化插件管理功能所需的权限定义：
- tenant:plugin:read - 查看插件定义
- tenant:plugin:write - 管理插件定义（注册、标记、删除）
- ai:plugin:read - 查看插件
- ai:plugin:write - 管理插件（安装、启动、停止、配置）
- ai:plugin:delete - 卸载插件
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from framework.utils.log_util import write_info, write_success, write_warning
from iam.models import Permission

# 插件管理权限定义
PLUGIN_PERMISSIONS = [
    {
        "code": "tenant:plugin:read",
        "name": "查看插件定义",
        "resource": "tenant:plugin",
        "action": "read",
        "description": "查看插件定义列表和详情",
    },
    {
        "code": "tenant:plugin:write",
        "name": "管理插件定义",
        "resource": "tenant:plugin",
        "action": "write",
        "description": "注册、标记推荐/禁用、删除插件定义",
    },
    {
        "code": "ai:plugin:read",
        "name": "查看插件",
        "resource": "ai:plugin",
        "action": "read",
        "description": "查看可用插件列表、安装任务、运行时状态",
    },
    {
        "code": "ai:plugin:write",
        "name": "管理插件",
        "resource": "ai:plugin",
        "action": "write",
        "description": "安装插件、启动/停止插件、更新配置",
    },
    {
        "code": "ai:plugin:delete",
        "name": "卸载插件",
        "resource": "ai:plugin",
        "action": "delete",
        "description": "卸载已安装的插件",
    },
]


async def run(*, dry_run: bool = False) -> int:
    """初始化插件管理权限数据

    创建插件管理功能所需的权限定义。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.database.core.engine import get_session

    async with get_session() as session:
        created_count = 0

        for perm_data in PLUGIN_PERMISSIONS:
            # 检查权限是否已存在
            result = await session.execute(
                select(Permission).where(Permission.code == perm_data["code"]).limit(1)
            )
            existing = result.scalar_one_or_none()

            if existing:
                write_info(f"权限已存在，跳过: {perm_data['code']}")
                continue

            if dry_run:
                write_info(f"[DRY-RUN] 将创建权限: {perm_data['code']} - {perm_data['name']}")
                created_count += 1
                continue

            # 创建权限（全局权限，tenant_id 为 None）
            permission = Permission(
                id=str(uuid.uuid4()),
                tenant_id=None,  # 全局权限
                code=perm_data["code"],
                name=perm_data["name"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                description=perm_data["description"],
            )
            session.add(permission)
            created_count += 1
            write_success(f"创建权限: {perm_data['code']} - {perm_data['name']}")

        if not dry_run and created_count > 0:
            await session.commit()

        return created_count
