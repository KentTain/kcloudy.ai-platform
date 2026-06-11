"""
Tenant 模块数据模块数据初始化

初始化默认租户数据。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from framework.utils.log_util import write_info, write_success, write_warning
from tenant.models import Tenant, TenantStatus


async def run(*, dry_run: bool = False) -> int:
    """初始化租户数据

    创建默认租户（如果不存在）。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.configs import get_settings
    from framework.database.core.engine import get_session

    settings = get_settings()
    tenant_config = settings.tenant

    async with get_session() as session:
        # 检查是否已存在默认租户
        result = await session.execute(
            select(Tenant).where(Tenant.code == "default").limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing:
            write_info("默认租户已存在，跳过初始化")
            return 0

        # 创建默认租户
        default_tenant_id = tenant_config.default_tenant_id

        tenant = Tenant(
            id=default_tenant_id,
            name="默认租户",
            code="default",
            status=TenantStatus.ACTIVE,
            contact_name="系统管理员",
            contact_email="admin@example.com",
            expired_at=datetime.now() + timedelta(days=365),
            settings={
                "max_users": 100,
                "max_storage_mb": 10240,
            },
            # 资源配置关联（可选，使用资源表的配置 ID）
            # 默认租户使用共享资源，无需指定配置 ID
        )

        if dry_run:
            write_info(f"[DRY-RUN] 将创建租户: {tenant.name} (code={tenant.code})")
            return 1

        session.add(tenant)
        await session.commit()

        write_success(f"已创建租户: {tenant.name} (id={default_tenant_id})")
        return 1
