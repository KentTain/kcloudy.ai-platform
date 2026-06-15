"""
租户服务

提供租户的 CRUD 操作和缓存管理。
"""

from datetime import datetime
from typing import Any, TypeAlias

from loguru import logger
from sqlalchemy import select, func, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.models import (
    Tenant,
    TenantConfig,
    TenantAdmin,
    TenantStatus,
    DatabaseConfig,
    StorageConfig,
    CacheConfig,
    QueueConfig,
    PubSubConfig,
)
from framework.database.core.engine import async_session
from framework.tenant.cache import TenantCache
from framework.tenant.context import SimpleTenant
from framework.tenant.protocols import (
    TenantDatabaseConfig,
    TenantStorageConfig,
    TenantCacheConfig,
    TenantQueueConfig,
    TenantPubSubConfig,
)
from framework.tenant.enums import DatabaseType, StorageType, QueueType, PubSubType
from framework.tenant.exceptions import (
    TenantNotFoundError,
    TenantInactiveError,
    TenantExpiredError,
)
from framework.utils.crypto import (
    generate_tenant_key,
    encrypt,
)
from framework.utils.resource_crypto import decrypt_password

_logger = logger.bind(name=__name__)

TenantRecord: TypeAlias = Tenant | SimpleTenant


class TenantService:
    """租户服务"""

    @staticmethod
    async def _load_database_config(config_id: str | None) -> TenantDatabaseConfig | None:
        """加载数据库配置"""
        if not config_id:
            return None
        async with async_session() as session:
            stmt = select(DatabaseConfig).where(DatabaseConfig.id == config_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            if not config:
                return None
            return TenantDatabaseConfig(
                type=DatabaseType(config.type),
                host=config.host,
                port=config.port,
                database=config.database,
                username=config.username,
                password=decrypt_password(config.password) if config.password else "",
            )

    @staticmethod
    async def _load_storage_config(config_id: str | None) -> TenantStorageConfig | None:
        """加载存储配置"""
        if not config_id:
            return None
        async with async_session() as session:
            stmt = select(StorageConfig).where(StorageConfig.id == config_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            if not config:
                return None
            return TenantStorageConfig(
                type=StorageType(config.type),
                endpoint=config.endpoint or "",
                access_key=config.access_key or "",
                secret_key=decrypt_password(config.secret_key) if config.secret_key else "",
                bucket=config.bucket,
            )

    @staticmethod
    async def _load_cache_config(config_id: str | None) -> TenantCacheConfig | None:
        """加载缓存配置"""
        if not config_id:
            return None
        async with async_session() as session:
            stmt = select(CacheConfig).where(CacheConfig.id == config_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            if not config:
                return None
            return TenantCacheConfig(
                host=config.host,
                port=config.port,
                password=decrypt_password(config.password) if config.password else "",
                db=config.db,
                prefix=config.prefix or "",
            )

    @staticmethod
    async def _load_queue_config(config_id: str | None) -> TenantQueueConfig | None:
        """加载队列配置"""
        if not config_id:
            return None
        async with async_session() as session:
            stmt = select(QueueConfig).where(QueueConfig.id == config_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            if not config:
                return None
            return TenantQueueConfig(
                type=QueueType(config.type),
                host=config.host,
                port=config.port,
                username=config.username or "",
                password=decrypt_password(config.password) if config.password else "",
                vhost=config.vhost or "/",
            )

    @staticmethod
    async def _load_pubsub_config(config_id: str | None) -> TenantPubSubConfig | None:
        """加载发布订阅配置"""
        if not config_id:
            return None
        async with async_session() as session:
            stmt = select(PubSubConfig).where(PubSubConfig.id == config_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            if not config:
                return None
            return TenantPubSubConfig(
                type=PubSubType(config.type),
                host=config.host,
                port=config.port,
                username=config.username or "",
                password=decrypt_password(config.password) if config.password else "",
            )

    @staticmethod
    async def build_simple_tenant(tenant: Tenant) -> SimpleTenant:
        """
        从 Tenant 模型构建 SimpleTenant，包括加载关联的资源配置

        Args:
            tenant: Tenant ORM 模型实例

        Returns:
            SimpleTenant: 包含完整资源配置的租户信息
        """
        # 并行加载所有资源配置
        import asyncio
        db_config, storage_config, cache_config, queue_config, pubsub_config = await asyncio.gather(
            TenantService._load_database_config(tenant.db_config_id),
            TenantService._load_storage_config(tenant.storage_config_id),
            TenantService._load_cache_config(tenant.cache_config_id),
            TenantService._load_queue_config(tenant.queue_config_id),
            TenantService._load_pubsub_config(tenant.pubsub_config_id),
        )
        return SimpleTenant.from_model(
            tenant,
            database=db_config,
            storage=storage_config,
            cache=cache_config,
            queue=queue_config,
            pubsub=pubsub_config,
        )

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

            if tenant:
                # 构建完整的 SimpleTenant（包含资源配置）
                simple_tenant = await TenantService.build_simple_tenant(tenant)
                if use_cache:
                    # 写入缓存
                    await TenantCache.set(simple_tenant)
                return simple_tenant

            return None

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
        # 资源配置关联
        db_config_id: str | None = None,
        storage_config_id: str | None = None,
        cache_config_id: str | None = None,
        queue_config_id: str | None = None,
        pubsub_config_id: str | None = None,
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
            db_config_id: 数据库配置 ID
            storage_config_id: 存储配置 ID
            cache_config_id: 缓存配置 ID
            queue_config_id: 队列配置 ID
            pubsub_config_id: 发布订阅配置 ID

        Returns:
            Tenant
        """
        # 生成租户加密密钥
        tenant_key = generate_tenant_key()
        # 用主密钥加密租户密钥
        encrypted_tenant_key = encrypt(tenant_key)

        async with async_session() as session:
            tenant = Tenant(
                name=name,
                code=code,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone,
                expired_at=expired_at,
                settings=settings or {},
                # 资源配置关联
                db_config_id=db_config_id,
                storage_config_id=storage_config_id,
                cache_config_id=cache_config_id,
                queue_config_id=queue_config_id,
                pubsub_config_id=pubsub_config_id,
                # 加密密钥
                encryption_key=encrypted_tenant_key,
            )
            session.add(tenant)
            await session.flush()  # 获取 tenant.id，但不提交

            # 自动分配活跃模块（通过 Protocol，避免 Tenant → IAM 依赖）
            from framework.tenant.protocols import get_module_auto_assigner

            assigner = get_module_auto_assigner()
            if assigner:
                await assigner.auto_assign(session, tenant.id)

            await session.commit()  # 原子提交
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
        更新租户基础信息

        Args:
            tenant_id: 租户 ID
            name: 租户名称
            contact_name: 联系人姓名
            contact_email: 联系人邮箱
            contact_phone: 联系人电话
            expired_at: 过期时间
            settings: 扩展设置

        Returns:
            Tenant | None

        Note:
            资源配置绑定请使用 update_resource_bindings 方法
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
    async def get_tenants_batch(tenant_ids: list[str]) -> list[Tenant]:
        """
        批量获取租户

        Args:
            tenant_ids: 租户 ID 列表

        Returns:
            list[Tenant]: 租户列表（顺序与请求一致）
        """
        if not tenant_ids:
            return []

        async with async_session() as session:
            stmt = select(Tenant).where(Tenant.id.in_(tenant_ids))
            result = await session.execute(stmt)
            tenants_map = {t.id: t for t in result.scalars().all()}

            # 按请求顺序返回
            return [tenants_map.get(tid) for tid in tenant_ids if tid in tenants_map]

    @staticmethod
    async def get_resource_bindings(tenant_id: str) -> Tenant | None:
        """
        获取租户的资源绑定情况

        Args:
            tenant_id: 租户 ID

        Returns:
            Tenant | None: 租户对象（包含资源配置 ID）
        """
        async with async_session() as session:
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def update_resource_bindings(
        tenant_id: str,
        db_config_id: str | None = None,
        storage_config_id: str | None = None,
        cache_config_id: str | None = None,
        queue_config_id: str | None = None,
        pubsub_config_id: str | None = None,
    ) -> Tenant | None:
        """
        更新租户的资源绑定

        Args:
            tenant_id: 租户 ID
            db_config_id: 数据库配置 ID（None 表示解绑）
            storage_config_id: 存储配置 ID
            cache_config_id: 缓存配置 ID
            queue_config_id: 队列配置 ID
            pubsub_config_id: 发布订阅配置 ID

        Returns:
            Tenant | None: 更新后的租户对象
        """
        async with async_session() as session:
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()

            if not tenant:
                return None

            # 更新资源绑定
            tenant.db_config_id = db_config_id
            tenant.storage_config_id = storage_config_id
            tenant.cache_config_id = cache_config_id
            tenant.queue_config_id = queue_config_id
            tenant.pubsub_config_id = pubsub_config_id

            await session.commit()
            await session.refresh(tenant)

            # 使缓存失效
            await TenantCache.invalidate(tenant_id)

            _logger.info(f"更新租户资源绑定: {tenant_id}")
            return tenant


# 服务单例
tenant_service = TenantService()
