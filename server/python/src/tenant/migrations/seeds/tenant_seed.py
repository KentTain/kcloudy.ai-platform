"""
Tenant 模块种子数据初始化

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
    如果默认租户已存在但未分配模块，也会补充分配。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.configs import get_settings
    from framework.database.core.engine import get_session
    from framework.events import ModuleAssigned, event_publisher
    from iam.services.module_sync_service import module_sync_service

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

        # 查询所有活跃模块
        module_result = await session.execute(
            select(Module).where(Module.is_active == True)
        )
        active_modules = list(module_result.scalars().all())

        if not active_modules:
            write_info("无活跃模块需要分配")
            return created_count or 0

        # 为默认租户分配所有活跃模块
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

            if dry_run:
                write_info(f"[DRY-RUN] 将为租户分配模块: {module.code}")
                continue

            # 创建租户模块关联
            tenant_module = TenantModule(
                tenant_id=default_tenant_id,
                module_id=module.id,
                is_active=True,
                started_at=datetime.now(),
            )
            session.add(tenant_module)
            await session.flush()

            # 直接同步模块数据到租户实例层（不依赖事件机制）
            await module_sync_service.sync_module_assigned(
                session, default_tenant_id, module.id, module.code
            )
            assigned_count += 1
            write_success(f"  已分配模块: {module.code}")

        if not dry_run:
            await session.commit()

        if created_count:
            write_success(f"已创建默认租户")
        if assigned_count:
            write_success(f"已分配 {assigned_count} 个模块")

        if not created_count and not assigned_count:
            write_info("默认租户已初始化且模块已分配，无需变更")

        return created_count + assigned_count
