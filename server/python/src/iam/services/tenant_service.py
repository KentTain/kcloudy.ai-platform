"""
租户服务

提供租户的 CRUD 操作和缓存管理。
"""

from datetime import datetime
from typing import Any, TypeAlias

from loguru import logger
from sqlalchemy import select, func, update, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import Tenant, TenantConfig, TenantAdmin, UserTenant, TenantStatus
from framework.database.core.engine import async_session
from framework.tenant.cache import TenantCache
from framework.tenant.context import SimpleTenant
from framework.tenant.exceptions import (
    TenantNotFoundError,
    TenantInactiveError,
    TenantExpiredError,
)
from framework.utils.crypto import (
    generate_tenant_key,
    encrypt,
    decrypt,
    get_master_key,
)

_logger = logger.bind(name=__name__)

TenantRecord: TypeAlias = Tenant | SimpleTenant


class TenantService:
    """租户服务"""

    @staticmethod
    async def get_by_id(tenant_id: str, use_cache: bool = True) -> TenantRecord | None:
        """
        根据 ID 获取租户

        Args:
            tenant_id: 租户 ID
            use_cache: 是否使用缓存

        Returns:
            TenantRecord | None（缓存命中为 SimpleTenant，否则为 ORM Tenant）
        """
        # 尝试从缓存获取
        if use_cache:
            cached = await TenantCache.get(tenant_id)
            if cached:
                return cached
        
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
        # 资源配置
        db_type: str | None = None,
        db_host: str | None = None,
        db_port: int | None = None,
        db_name: str | None = None,
        db_username: str | None = None,
        db_password: str | None = None,
        storage_type: str | None = None,
        storage_bucket: str | None = None,
        cache_db: int | None = None,
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
            db_type: 数据库类型
            db_host: 数据库主机
            db_port: 数据库端口
            db_name: 数据库名称
            db_username: 数据库用户名
            db_password: 数据库密码（明文，会自动加密）
            storage_type: 存储类型
            storage_bucket: 存储桶名称
            cache_db: Redis DB 编号

        Returns:
            Tenant
        """
        # 生成租户加密密钥
        tenant_key = generate_tenant_key()
        # 用主密钥加密租户密钥
        encrypted_tenant_key = encrypt(tenant_key)

        # 加密数据库密码
        encrypted_db_password = None
        if db_password:
            encrypted_db_password = encrypt(db_password)

        async with async_session() as session:
            tenant = Tenant(
                name=name,
                code=code,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone,
                expired_at=expired_at,
                settings=settings or {},
                # 数据库配置
                db_type=db_type,
                db_host=db_host,
                db_port=db_port,
                db_name=db_name,
                db_username=db_username,
                db_password=encrypted_db_password,
                # 存储配置
                storage_type=storage_type,
                storage_bucket=storage_bucket,
                # 缓存配置
                cache_db=cache_db,
                # 加密密钥
                encryption_key=encrypted_tenant_key,
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
        # 资源配置
        db_type: str | None = None,
        db_host: str | None = None,
        db_port: int | None = None,
        db_name: str | None = None,
        db_username: str | None = None,
        db_password: str | None = None,
        storage_type: str | None = None,
        storage_bucket: str | None = None,
        cache_db: int | None = None,
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

            # 更新数据库配置
            if db_type is not None:
                tenant.db_type = db_type
            if db_host is not None:
                tenant.db_host = db_host
            if db_port is not None:
                tenant.db_port = db_port
            if db_name is not None:
                tenant.db_name = db_name
            if db_username is not None:
                tenant.db_username = db_username
            if db_password is not None:
                # 加密数据库密码
                tenant.db_password = encrypt(db_password) if db_password else None

            # 更新存储配置
            if storage_type is not None:
                tenant.storage_type = storage_type
            if storage_bucket is not None:
                tenant.storage_bucket = storage_bucket

            # 更新缓存配置
            if cache_db is not None:
                tenant.cache_db = cache_db

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
    async def validate_tenant(tenant_id: str) -> TenantRecord:
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
