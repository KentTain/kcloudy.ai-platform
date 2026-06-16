"""
管理员模块数据初始化

初始化默认管理员账户。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from framework.utils.log_util import write_info, write_success, write_warning
from tenant.models import TenantAdmin


async def run(*, dry_run: bool = False) -> int:
    """初始化管理员数据

    创建默认管理员账户（如果不存在）。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.database.core.engine import get_session
    from framework.utils.crypto import hash_password

    async with get_session() as session:
        # 检查是否已存在默认管理员
        result = await session.execute(
            select(TenantAdmin).where(TenantAdmin.is_default == True).limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing:
            write_warning("默认管理员已存在，跳过初始化")
            return 0

        # 创建默认管理员
        admin_id = str(uuid.uuid4())

        # 默认密码: admin123 (生产环境应使用环境变量或配置文件)
        default_password = "admin123"
        password_hash = hash_password(default_password)

        admin = TenantAdmin(
            id=admin_id,
            username="admin",
            password=password_hash,
            is_default=True,
            is_active=True,
        )

        if dry_run:
            write_info(f"    [DRY-RUN] 将创建管理员: {admin.username}")
            write_info(f"    [DRY-RUN] 默认密码: {default_password}")
            return 1

        session.add(admin)
        await session.commit()

        write_success(f"    已创建管理员: {admin.username}")
        write_success(f"    默认密码: {default_password}")
        write_warning("    [WARN] 请在生产环境中修改默认密码!")
        return 1
