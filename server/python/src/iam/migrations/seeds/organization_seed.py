"""
组织种子数据初始化

为默认租户创建默认顶级组织。
组织名称和编码使用租户的名称和编码。
负责人（leader_id）在用户种子中设置。
"""

from __future__ import annotations

from sqlalchemy import select

from framework.utils.log_util import write_info, write_success, write_warning
from iam.models import Organization


async def run(*, dry_run: bool = False) -> int:
    """初始化默认组织数据

    为默认租户创建默认顶级组织。
    组织名称和编码使用租户的名称和编码。
    负责人（leader_id）在用户种子中设置。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.configs import get_settings
    from framework.database.core.engine import get_session

    settings = get_settings()
    tenant_id = settings.tenant.default_tenant_id

    async with get_session() as session:
        # 检查是否已存在默认组织
        result = await session.execute(
            select(Organization).where(
                Organization.tenant_id == tenant_id,
                Organization.code == "default",
            ).limit(1)
        )
        existing_org = result.scalar_one_or_none()

        if existing_org:
            write_warning("默认组织已存在，跳过初始化")
            return 0

        # 种子数据特殊场景：需跨模块查询 tenant.models.Tenant，
        # 使用局部导入避免模块级循环依赖
        from tenant.models import Tenant

        tenant_result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id).limit(1)
        )
        tenant = tenant_result.scalar_one_or_none()

        tenant_name = tenant.name if tenant else "默认租户"
        tenant_code = tenant.code if tenant else "default"

        if dry_run:
            write_info(f"[DRY-RUN] 将创建默认组织: {tenant_name} (code={tenant_code})")
            return 1

        # 使用 create_node 创建组织（自动维护树字段）
        org = await Organization.create_node(
            session,
            source={
                "tenant_id": tenant_id,
                "name": tenant_name,
                "code": tenant_code,
                "parent_id": None,  # 顶级组织
                "status": "active",
                "sort_order": 0,
            },
            extra_conditions=[Organization.tenant_id == tenant_id],
        )

        await session.commit()

        write_success(f"已创建默认组织: {org.name} (id={org.id})")
        return 1
