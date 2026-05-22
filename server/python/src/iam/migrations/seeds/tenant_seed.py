"""
租户模块数据初始化

初始化默认租户数据。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from iam.models import Tenant, TenantStatus


async def run(*, dry_run: bool = False) -> int:
    """初始化租户数据

    创建默认租户（如果不存在）。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.database.core.engine import get_session
    from framework.configs import get_settings
    from framework.utils.crypto import encrypt

    settings = get_settings()
    tenant_config = settings.tenant

    async with get_session() as session:
        # 检查是否已存在默认租户
        result = await session.execute(
            select(Tenant).where(Tenant.code == "default").limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("    默认租户已存在，跳过初始化")
            return 0

        # 创建默认租户
        tenant_id = str(uuid.uuid4())

        # 从配置读取资源隔离参数（可选）
        db_password_encrypted = None
        if tenant_config.default_db_password:
            db_password_encrypted = encrypt(tenant_config.default_db_password)

        tenant = Tenant(
            id=tenant_id,
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
            # 资源配置（可选物理隔离）
            db_type=tenant_config.default_db_type,
            db_host=tenant_config.default_db_host,
            db_port=tenant_config.default_db_port,
            db_name=tenant_config.default_db_name,
            db_username=tenant_config.default_db_username,
            db_password=db_password_encrypted,
            storage_type=tenant_config.default_storage_type,
            storage_bucket=tenant_config.default_storage_bucket,
            cache_db=tenant_config.default_cache_db,
        )

        if dry_run:
            print(f"    [DRY-RUN] 将创建租户: {tenant.name} (code={tenant.code})")
            return 1

        session.add(tenant)
        await session.commit()

        print(f"    已创建租户: {tenant.name} (id={tenant_id})")
        return 1
