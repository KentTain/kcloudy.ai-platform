"""
Tenant 模块种子数据初始化

初始化默认租户数据并分配活跃模块。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from framework.utils.log_util import write_info, write_success, write_warning
from tenant.models import Tenant, TenantStatus


async def run(*, dry_run: bool = False) -> int:
    """初始化租户数据

    创建默认租户（如果不存在）并分配所有活跃模块。
    如果默认租户已存在但未分配模块，也会补充分配。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.configs import get_settings
    from framework.database.core.engine import get_session
    from framework.tenant.protocols import get_module_auto_assigner

    settings = get_settings()
    tenant_config = settings.tenant
    default_tenant_id = tenant_config.default_tenant_id

    created_count = 0
    assigned_count = 0

    async with get_session() as session:
        # 检查是否已存在默认租户
        result = await session.execute(
            select(Tenant).where(Tenant.code == "default").limit(1)
        )
        existing_tenant = result.scalar_one_or_none()

        if existing_tenant:
            write_info("默认租户已存在，跳过创建")
        else:
            # 创建默认租户
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
            )

            if dry_run:
                write_info(f"[DRY-RUN] 将创建租户: {tenant.name} (code={tenant.code})")
                return 1

            session.add(tenant)
            await session.flush()
            created_count += 1
            write_success(f"已创建租户: {tenant.name} (id={default_tenant_id})")

        # 通过 Protocol 自动分配活跃模块（同一事务，避免 Tenant → IAM 依赖）
        assigner = get_module_auto_assigner()
        if assigner:
            if dry_run:
                write_info("[DRY-RUN] 将为租户分配所有活跃模块")
            else:
                await assigner.auto_assign(session, default_tenant_id)
                assigned_count = 1  # 标记分配成功，具体数量由 assigner 日志体现

        if not dry_run:
            await session.commit()

        if created_count:
            write_success(f"已创建默认租户")
        if assigned_count:
            write_success(f"已为默认租户分配活跃模块")

        if not created_count and not assigned_count:
            write_info("默认租户已初始化且模块已分配，无需变更")

        return created_count + (1 if assigned_count else 0)
