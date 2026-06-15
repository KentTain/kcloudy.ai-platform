"""
Tenant 模块数据模块数据初始化

初始化默认租户数据并分配活跃模块。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from framework.utils.log_util import write_info, write_success, write_warning
from tenant.models import Module, Tenant, TenantModule, TenantStatus


async def run(*, dry_run: bool = False) -> int:
    """初始化租户数据

    创建默认租户（如果不存在）并分配所有活跃模块。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.configs import get_settings
    from framework.database.core.engine import get_session
    from framework.events import ModuleAssigned, event_publisher

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
        await session.flush()  # 确保 tenant.id 可用

        # 查询所有活跃模块
        module_result = await session.execute(
            select(Module).where(Module.is_active == True)
        )
        active_modules = list(module_result.scalars().all())

        # 为租户分配所有活跃模块
        assigned_count = 0
        for module in active_modules:
            # 检查是否已分配
            existing_tm = await session.execute(
                select(TenantModule).where(
                    TenantModule.tenant_id == default_tenant_id,
                    TenantModule.module_id == module.id,
                )
            )
            if existing_tm.scalar_one_or_none():
                continue

            # 创建租户模块关联
            tenant_module = TenantModule(
                tenant_id=default_tenant_id,
                module_id=module.id,
                is_active=True,
                started_at=datetime.now(),
            )
            session.add(tenant_module)
            assigned_count += 1

            # 发布 ModuleAssigned 事件以触发模块同步
            await event_publisher.publish(
                ModuleAssigned(tenant_id=default_tenant_id, module_id=module.id)
            )

        await session.commit()

        write_success(f"已创建租户: {tenant.name} (id={default_tenant_id})")
        if assigned_count > 0:
            write_success(f"已为租户分配 {assigned_count} 个模块")

        return 1
