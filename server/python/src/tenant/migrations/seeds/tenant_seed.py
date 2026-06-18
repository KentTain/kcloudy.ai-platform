"""
Tenant 模块种子数据初始化

初始化默认租户数据并分配活跃模块。
创建租户时自动关联默认资源配置（如果存在）。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from framework.utils.log_util import write_info, write_success, write_warning
from tenant.models import (
    CacheConfig,
    DatabaseConfig,
    PubSubConfig,
    QueueConfig,
    StorageConfig,
    Tenant,
    TenantStatus,
)


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
            # 查询默认资源配置（is_default=True）
            default_db = await session.execute(
                select(DatabaseConfig).where(DatabaseConfig.is_default == True).limit(1)  # noqa: E712
            )
            default_db_config = default_db.scalar_one_or_none()

            default_cache = await session.execute(
                select(CacheConfig).where(CacheConfig.is_default == True).limit(1)  # noqa: E712
            )
            default_cache_config = default_cache.scalar_one_or_none()

            default_storage = await session.execute(
                select(StorageConfig).where(StorageConfig.is_default == True).limit(1)  # noqa: E712
            )
            default_storage_config = default_storage.scalar_one_or_none()

            default_queue = await session.execute(
                select(QueueConfig).where(QueueConfig.is_default == True).limit(1)  # noqa: E712
            )
            default_queue_config = default_queue.scalar_one_or_none()

            default_pubsub = await session.execute(
                select(PubSubConfig).where(PubSubConfig.is_default == True).limit(1)  # noqa: E712
            )
            default_pubsub_config = default_pubsub.scalar_one_or_none()

            # 创建默认租户，关联默认资源配置
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
                # 关联默认资源配置
                db_config_id=default_db_config.id if default_db_config else None,
                cache_config_id=default_cache_config.id if default_cache_config else None,
                storage_config_id=default_storage_config.id if default_storage_config else None,
                queue_config_id=default_queue_config.id if default_queue_config else None,
                pubsub_config_id=default_pubsub_config.id if default_pubsub_config else None,
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
            write_warning("默认租户已初始化且模块已分配，无需变更")

        return created_count + (1 if assigned_count else 0)
