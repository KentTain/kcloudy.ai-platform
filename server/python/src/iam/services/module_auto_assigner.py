"""
模块自动分配器实现

为租户自动分配所有活跃模块，避免 Tenant → IAM 循环依赖。
"""

from datetime import datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.models import Module, TenantModule

_logger = logger.bind(name=__name__)


class IamModuleAutoAssigner:
    """IAM 模块自动分配器"""

    async def auto_assign(self, session: AsyncSession, tenant_id: str) -> None:
        """
        为租户自动分配所有活跃模块

        Args:
            session: 当前数据库会话
            tenant_id: 租户 ID
        """
        from iam.services.module_sync_service import module_sync_service

        # 查询所有活跃模块
        result = await session.execute(
            select(Module).where(Module.is_active == True)
        )
        modules = list(result.scalars().all())

        if not modules:
            _logger.info(f"无活跃模块需要分配: tenant_id={tenant_id}")
            return

        assigned_count = 0
        for module in modules:
            # 幂等检查
            existing = await session.execute(
                select(TenantModule).where(
                    TenantModule.tenant_id == tenant_id,
                    TenantModule.module_id == module.id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            # 创建 TenantModule 记录
            tenant_module = TenantModule(
                tenant_id=tenant_id,
                module_id=module.id,
                is_active=True,
                started_at=datetime.now(),
            )
            session.add(tenant_module)
            await session.flush()

            # 同步到租户实例层
            await module_sync_service.sync_module_assigned(
                session, tenant_id, module.id, module.code
            )
            assigned_count += 1
            _logger.info(f"  已分配模块: {module.code} (tenant_id={tenant_id})")

        _logger.info(
            f"模块自动分配完成: tenant_id={tenant_id}, count={assigned_count}"
        )
