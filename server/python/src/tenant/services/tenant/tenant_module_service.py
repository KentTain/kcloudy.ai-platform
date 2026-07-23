"""
租户模块分配服务层
"""

import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.clients.iam_client import get_iam_client
from framework.events import ModuleAssigned, ModuleUnassigned, event_publisher
from tenant.models import Module, ModuleRole, TenantModule

_logger = logging.getLogger(__name__)


class TenantModuleService:
    """租户模块分配服务"""

    @staticmethod
    async def list_tenant_modules(
        session: AsyncSession,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TenantModule], int]:
        """
        查询租户已分配的模块列表

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            page: 页码
            page_size: 每页数量

        Returns:
            (租户模块列表, 总数)
        """
        # 查询总数
        count_stmt = select(func.count(TenantModule.id)).where(
            TenantModule.tenant_id == tenant_id
        )
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        stmt = (
            select(TenantModule)
            .where(TenantModule.tenant_id == tenant_id)
            .order_by(TenantModule.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await session.execute(stmt)
        tenant_modules = list(result.scalars().all())

        return tenant_modules, total

    @staticmethod
    async def get_tenant_module(session: AsyncSession, tenant_id: str, module_id: str) -> TenantModule | None:
        """
        获取租户模块分配记录

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            module_id: 模块 ID

        Returns:
            TenantModule | None
        """
        stmt = select(TenantModule).where(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_id == module_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def assign_module(
        session: AsyncSession,
        tenant_id: str,
        module_id: str,
        started_at: datetime,
        expired_at: datetime | None = None,
    ) -> TenantModule:
        """
        为租户分配模块

        业务规则：
        1. 校验模块存在且 is_active=true
        2. 校验该租户未已分配该模块
        3. 如果模块 is_need=true，分配时不可设置过期时间
        4. 创建 TenantModule 记录
        5. 发布 ModuleAssigned 事件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            module_id: 模块 ID
            started_at: 生效时间
            expired_at: 过期时间（可选）

        Returns:
            TenantModule

        Raises:
            ValueError: 业务校验失败
        """
        # 1. 校验模块存在且已启用
        module_stmt = select(Module).where(Module.id == module_id)
        module_result = await session.execute(module_stmt)
        module = module_result.scalar_one_or_none()

        if not module:
            raise ValueError(f"模块不存在: {module_id}")

        if not module.is_active:
            raise ValueError(f"模块未启用: {module.code}")

        # 2. 校验租户未已分配该模块
        existing_stmt = select(TenantModule).where(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_id == module_id,
        )
        existing_result = await session.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise ValueError(f"租户已分配该模块: {module.code}")

        # 3. 如果模块 is_need=true，不允许设置过期时间
        if module.is_need and expired_at is not None:
            raise ValueError(f"必须模块（{module.code}）不允许设置过期时间")

        # 4. 创建 TenantModule 记录
        tenant_module = TenantModule(
            tenant_id=tenant_id,
            module_id=module_id,
            started_at=started_at,
            expired_at=expired_at,
            is_active=True,
        )
        session.add(tenant_module)
        await session.flush()
        await session.refresh(tenant_module)

        _logger.info(
            f"租户 {tenant_id} 分配模块 {module.code}，"
            f"生效时间: {started_at}，过期时间: {expired_at or '无'}"
        )

        # 5. 发布 ModuleAssigned 事件
        await event_publisher.publish(
            ModuleAssigned(tenant_id=tenant_id, module_id=module_id)
        )

        return tenant_module

    @staticmethod
    async def unassign_module(session: AsyncSession, tenant_id: str, module_id: str) -> bool:
        """
        取消租户的模块分配

        业务规则：
        1. 校验模块不是必须模块（is_need=false）
        2. 检查租户实例层是否有用户使用该模块的角色
        3. 有用户使用 -> 返回错误；无用户使用 -> 继续
        4. 删除 TenantModule 记录
        5. 发布 ModuleUnassigned 事件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            module_id: 模块 ID

        Returns:
            bool: 是否取消成功

        Raises:
            ValueError: 业务校验失败
        """
        # 查询模块信息
        module_stmt = select(Module).where(Module.id == module_id)
        module_result = await session.execute(module_stmt)
        module = module_result.scalar_one_or_none()

        if not module:
            raise ValueError(f"模块不存在: {module_id}")

        # 1. 校验模块不是必须模块
        if module.is_need:
            raise ValueError(f"必须模块（{module.code}）禁止取消分配")

        # 查询租户模块分配记录
        tm_stmt = select(TenantModule).where(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_id == module_id,
        )
        tm_result = await session.execute(tm_stmt)
        tenant_module = tm_result.scalar_one_or_none()

        if not tenant_module:
            return False

        # 2. 检查租户实例层是否有用户使用该模块的角色
        await TenantModuleService._check_module_role_usage(
            session, tenant_id, module_id, module.code
        )

        # 4. 删除 TenantModule 记录
        await session.delete(tenant_module)
        await session.flush()

        _logger.info(f"租户 {tenant_id} 取消分配模块 {module.code}")

        # 5. 发布 ModuleUnassigned 事件
        await event_publisher.publish(
            ModuleUnassigned(tenant_id=tenant_id, module_id=module_id)
        )

        return True

    @staticmethod
    async def _check_module_role_usage(
        session: AsyncSession, tenant_id: str, module_id: str, module_code: str
    ) -> None:
        """
        检查租户下是否有用户使用该模块的角色

        检查逻辑：
        1. 查询该模块的所有 ModuleRole
        2. 通过 Role.ref_id 找到租户实例层对应的角色
        3. 检查 UserRole 表是否有用户关联这些角色

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            module_id: 模块 ID
            module_code: 模块编码（用于错误消息）

        Raises:
            ValueError: 有用户使用该模块的角色
        """
        # 1. 查询该模块的所有 ModuleRole ID
        role_stmt = select(ModuleRole.id).where(ModuleRole.module_id == module_id)
        role_result = await session.execute(role_stmt)
        module_role_ids = [row[0] for row in role_result.all()]

        if not module_role_ids:
            # 该模块没有定义角色，可以直接取消
            return

        # 2. 通过 iam_client 检查角色使用情况
        iam_client = get_iam_client()
        usage_list = await iam_client.check_module_role_usage(
            tenant_id, module_role_ids
        )

        if usage_list:
            # 有用户正在使用该模块的角色
            role_details = ", ".join(
                f"{u.role_name}({u.user_count}人)" for u in usage_list
            )
            raise ValueError(
                f"模块 {module_code} 的角色正在被使用: {role_details}，"
                f"请先移除相关用户的角色后再取消分配"
            )

    @staticmethod
    async def get_module_with_info(session: AsyncSession, tenant_module: TenantModule) -> dict:
        """
        获取租户模块的完整信息（包含模块详情）

        Args:
            session: 数据库会话
            tenant_module: 租户模块分配记录

        Returns:
            dict: 包含 tenant_module 和 module 信息的字典
        """
        stmt = select(Module).where(Module.id == tenant_module.module_id)
        result = await session.execute(stmt)
        module = result.scalar_one_or_none()

        return {
            "tenant_module": tenant_module,
            "module": module,
        }


# 单例实例
tenant_module_service = TenantModuleService()
