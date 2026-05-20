"""
租户服务

提供租户的 CRUD 操作和缓存管理。
"""

from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import select, func, update, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from demo.models.tenant import Tenant, TenantConfig, TenantAdmin, UserTenant, TenantStatus
from demo.models.core.engine import async_session
from framework.tenant.cache import TenantCache
from framework.tenant.context import SimpleTenant
from framework.tenant.exceptions import (
    TenantNotFoundError,
    TenantInactiveError,
    TenantExpiredError,
)

_logger = logger.bind(name=__name__)


class TenantService:
    """租户服务"""

    @staticmethod
    async def get_by_id(tenant_id: str, use_cache: bool = True) -> Tenant | None:
        """
        根据 ID 获取租户

        Args:
            tenant_id: 租户 ID
            use_cache: 是否使用缓存

        Returns:
            Tenant | None
        """
        # 尝试从缓存获取
        if use_cache:
            cached = await TenantCache.get(tenant_id)
            if cached:
                # 需要从数据库获取完整信息
                async with async_session() as session:
                    stmt = select(Tenant).where(Tenant.id == tenant_id)
                    result = await session.execute(stmt)
                    tenant = result.scalar_one_or_none()
                    return tenant

        # 从数据库获取
        async with async_session() as session:
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()

            if tenant and use_cache:
                # 写入缓存
                await TenantCache.set(SimpleTenant.from_model(tenant))

            return tenant

    @staticmethod
    async def get_by_code(code: str) -> Tenant | None:
        """根据编码获取租户"""
        async with async_session() as session:
            stmt = select(Tenant).where(Tenant.code == code)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def create(
        name: str,
        code: str,
        contact_name: str | None = None,
        contact_email: str | None = None,
        contact_phone: str | None = None,
        expired_at: datetime | None = None,
        settings: dict[str, Any] | None = None,
    ) -> Tenant:
        """
        创建租户

        Args:
            name: 租户名称
            code: 租户编码
            contact_name: 联系人姓名
            contact_email: 联系人邮箱
            contact_phone: 联系人电话
            expired_at: 过期时间
            settings: 扩展设置

        Returns:
            Tenant
        """
        async with async_session() as session:
            tenant = Tenant(
                name=name,
                code=code,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone,
                expired_at=expired_at,
                settings=settings or {},
            )
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)

            _logger.info(f"创建租户: {tenant.id} ({tenant.code})")
            return tenant

    @staticmethod
    async def update(
        tenant_id: str,
        name: str | None = None,
        contact_name: str | None = None,
        contact_email: str | None = None,
        contact_phone: str | None = None,
        expired_at: datetime | None = None,
        settings: dict[str, Any] | None = None,
    ) -> Tenant | None:
        """
        更新租户

        Args:
            tenant_id: 租户 ID
            其他参数为要更新的字段

        Returns:
            Tenant | None
        """
        async with async_session() as session:
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()

            if not tenant:
                return None

            if name is not None:
                tenant.name = name
            if contact_name is not None:
                tenant.contact_name = contact_name
            if contact_email is not None:
                tenant.contact_email = contact_email
            if contact_phone is not None:
                tenant.contact_phone = contact_phone
            if expired_at is not None:
                tenant.expired_at = expired_at
            if settings is not None:
                tenant.settings = settings

            await session.commit()
            await session.refresh(tenant)

            # 使缓存失效
            await TenantCache.invalidate(tenant_id)

            _logger.info(f"更新租户: {tenant_id}")
            return tenant

    @staticmethod
    async def delete(tenant_id: str) -> bool:
        """
        删除租户（软删除）

        Args:
            tenant_id: 租户 ID

        Returns:
            bool: 是否删除成功
        """
        async with async_session() as session:
            stmt = sql_delete(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount > 0:
                # 使缓存失效
                await TenantCache.invalidate(tenant_id)
                _logger.info(f"删除租户: {tenant_id}")
                return True
            return False

    @staticmethod
    async def activate(tenant_id: str) -> Tenant | None:
        """激活租户"""
        async with async_session() as session:
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()

            if not tenant:
                return None

            tenant.status = TenantStatus.ACTIVE
            await session.commit()
            await session.refresh(tenant)

            # 使缓存失效
            await TenantCache.invalidate(tenant_id)

            _logger.info(f"激活租户: {tenant_id}")
            return tenant

    @staticmethod
    async def deactivate(tenant_id: str) -> Tenant | None:
        """停用租户"""
        async with async_session() as session:
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()

            if not tenant:
                return None

            tenant.status = TenantStatus.INACTIVE
            await session.commit()
            await session.refresh(tenant)

            # 使缓存失效
            await TenantCache.invalidate(tenant_id)

            _logger.info(f"停用租户: {tenant_id}")
            return tenant

    @staticmethod
    async def validate_tenant(tenant_id: str) -> Tenant:
        """
        验证租户状态

        Args:
            tenant_id: 租户 ID

        Returns:
            Tenant

        Raises:
            TenantNotFoundError: 租户不存在
            TenantInactiveError: 租户已停用
            TenantExpiredError: 租户已过期
        """
        tenant = await TenantService.get_by_id(tenant_id)

        if not tenant:
            raise TenantNotFoundError(tenant_id)

        if tenant.status != TenantStatus.ACTIVE:
            raise TenantInactiveError(tenant_id)

        if tenant.expired_at and tenant.expired_at < datetime.now():
            raise TenantExpiredError(tenant_id)

        return tenant

    @staticmethod
    async def list_tenants(
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Tenant], int]:
        """
        获取租户列表（分页）

        Args:
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词（名称或编码）
            status: 状态过滤

        Returns:
            tuple[list[Tenant], int]: 租户列表和总数
        """
        async with async_session() as session:
            # 构建查询条件
            conditions = []
            if keyword:
                conditions.append(
                    (Tenant.name.ilike(f"%{keyword}%"))
                    | (Tenant.code.ilike(f"%{keyword}%"))
                )
            if status:
                conditions.append(Tenant.status == status)

            # 查询总数
            count_stmt = select(func.count(Tenant.id))
            if conditions:
                count_stmt = count_stmt.where(*conditions)
            total_result = await session.execute(count_stmt)
            total = total_result.scalar() or 0

            # 查询列表
            offset = (page - 1) * page_size
            stmt = select(Tenant)
            if conditions:
                stmt = stmt.where(*conditions)
            stmt = stmt.order_by(Tenant.created_at.desc()).offset(offset).limit(page_size)

            result = await session.execute(stmt)
            tenants = list(result.scalars().all())

            return tenants, total

    @staticmethod
    async def get_user_tenants(user_id: str) -> list[Tenant]:
        """
        获取用户所属的租户列表

        Args:
            user_id: 用户 ID

        Returns:
            list[Tenant]
        """
        async with async_session() as session:
            stmt = (
                select(Tenant)
                .join(UserTenant, Tenant.id == UserTenant.tenant_id)
                .where(UserTenant.user_id == user_id)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def add_user_to_tenant(
        user_id: str,
        tenant_id: str,
        role: str = "member",
        is_default: bool = False,
    ) -> UserTenant:
        """添加用户到租户"""
        async with async_session() as session:
            user_tenant = UserTenant(
                user_id=user_id,
                tenant_id=tenant_id,
                role=role,
                is_default=is_default,
            )
            session.add(user_tenant)
            await session.commit()
            await session.refresh(user_tenant)
            return user_tenant

    @staticmethod
    async def remove_user_from_tenant(user_id: str, tenant_id: str) -> bool:
        """从租户移除用户"""
        async with async_session() as session:
            stmt = sql_delete(UserTenant).where(
                UserTenant.user_id == user_id, UserTenant.tenant_id == tenant_id
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0


# 服务单例
tenant_service = TenantService()
