"""
数据库引擎池管理

提供租户级数据库连接池缓存管理，支持：
- 惰性加载
- LRU 回收
- 最大连接池数量限制
"""

from collections import OrderedDict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from framework.tenant.tenant_protocols import TenantDatabaseConfig

_logger = logger.bind(name=__name__)

# 默认配置
DEFAULT_POOL_SIZE = 10
DEFAULT_MAX_OVERFLOW = 20
DEFAULT_MAX_ENGINES = 50  # 最大缓存的引擎数量
DEFAULT_IDLE_TIMEOUT = 1800  # 空闲超时（秒），30 分钟


class DatabaseEnginePool:
    """
    数据库引擎池管理器

    管理：
    - 默认数据库引擎
    - 租户级独立数据库引擎
    - LRU 缓存回收
    """

    def __init__(
        self,
        max_engines: int = DEFAULT_MAX_ENGINES,
        idle_timeout: int = DEFAULT_IDLE_TIMEOUT,
    ):
        """
        初始化引擎池

        Args:
            max_engines: 最大缓存的引擎数量
            idle_timeout: 空闲超时（秒）
        """
        self._max_engines = max_engines
        self._idle_timeout = idle_timeout

        # 默认引擎
        self._default_engine: AsyncEngine | None = None
        self._default_session_factory: async_sessionmaker[AsyncSession] | None = None

        # 租户引擎缓存（按访问时间排序，用于 LRU）
        self._engines: OrderedDict[str, AsyncEngine] = OrderedDict()
        self._session_factories: dict[str, async_sessionmaker[AsyncSession]] = {}
        self._access_times: dict[str, datetime] = {}

        # 租户配置缓存
        self._configs: dict[str, TenantDatabaseConfig] = {}

        # 待清理的引擎列表（用于异步安全回收）
        self._pending_dispose: list[AsyncEngine] = []

    def init_default(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = DEFAULT_POOL_SIZE,
        max_overflow: int = DEFAULT_MAX_OVERFLOW,
    ) -> None:
        """
        初始化默认数据库引擎

        Args:
            database_url: 数据库连接 URL
            echo: 是否打印 SQL
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
        """
        if self._default_engine is not None:
            _logger.warning("默认数据库引擎已初始化，跳过重复初始化")
            return

        self._default_engine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
        )
        self._default_session_factory = async_sessionmaker(
            bind=self._default_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        _logger.info("默认数据库引擎初始化完成")

    def get_engine(
        self,
        tenant_id: str | None,
        config: TenantDatabaseConfig | None = None,
    ) -> AsyncEngine:
        """
        获取数据库引擎

        Args:
            tenant_id: 租户 ID（None 表示使用默认引擎）
            config: 租户数据库配置

        Returns:
            AsyncEngine: 数据库引擎
        """
        # 无租户 ID 或无配置，使用默认引擎
        if not tenant_id or not config or not config.database:
            if self._default_engine is None:
                raise RuntimeError("默认数据库引擎未初始化")
            return self._default_engine

        # 检查缓存
        if tenant_id in self._engines:
            # 更新访问时间（移到末尾）
            self._engines.move_to_end(tenant_id)
            self._access_times[tenant_id] = datetime.now()
            return self._engines[tenant_id]

        # 创建新引擎
        if config:
            engine = self._create_engine(config)
            self._add_engine(tenant_id, engine, config)
            return engine

        # 回退到默认引擎
        if self._default_engine is None:
            raise RuntimeError("默认数据库引擎未初始化")
        return self._default_engine

    def get_session_factory(
        self,
        tenant_id: str | None,
        config: TenantDatabaseConfig | None = None,
    ) -> async_sessionmaker[AsyncSession]:
        """
        获取会话工厂

        Args:
            tenant_id: 租户 ID
            config: 租户数据库配置

        Returns:
            async_sessionmaker: 会话工厂
        """
        # 无租户 ID 或无配置，使用默认会话工厂
        if not tenant_id or not config or not config.database:
            if self._default_session_factory is None:
                raise RuntimeError("默认数据库引擎未初始化")
            return self._default_session_factory

        # 确保引擎存在
        if tenant_id not in self._session_factories:
            self.get_engine(tenant_id, config)

        return self._session_factories[tenant_id]

    @asynccontextmanager
    async def session(
        self,
        tenant_id: str | None = None,
        config: TenantDatabaseConfig | None = None,
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话

        Args:
            tenant_id: 租户 ID
            config: 租户数据库配置

        Yields:
            AsyncSession: 数据库会话
        """
        session_factory = self.get_session_factory(tenant_id, config)
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def _create_engine(self, config: TenantDatabaseConfig) -> AsyncEngine:
        """
        创建数据库引擎

        Args:
            config: 数据库配置

        Returns:
            AsyncEngine: 数据库引擎
        """
        # 构建连接 URL
        url = self._build_database_url(config)

        return create_async_engine(
            url,
            echo=False,
            pool_size=DEFAULT_POOL_SIZE,
            max_overflow=DEFAULT_MAX_OVERFLOW,
            pool_pre_ping=True,
        )

    def _build_database_url(self, config: TenantDatabaseConfig) -> str:
        """
        构建数据库连接 URL

        Args:
            config: 数据库配置

        Returns:
            str: 数据库连接 URL
        """
        # 默认使用 asyncpg 驱动
        driver = "postgresql+asyncpg"
        if config.type.value == "mysql":
            driver = "mysql+aiomysql"
        elif config.type.value == "sqlite":
            driver = "sqlite+aiosqlite"

        return (
            f"{driver}://{config.username}:{config.password}"
            f"@{config.host}:{config.port}/{config.database}"
        )

    def _add_engine(
        self,
        tenant_id: str,
        engine: AsyncEngine,
        config: TenantDatabaseConfig,
    ) -> None:
        """
        添加引擎到缓存

        Args:
            tenant_id: 租户 ID
            engine: 数据库引擎
            config: 数据库配置
        """
        # 检查是否需要回收
        while len(self._engines) >= self._max_engines:
            self._evict_lru()

        # 添加到缓存
        self._engines[tenant_id] = engine
        self._session_factories[tenant_id] = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._access_times[tenant_id] = datetime.now()
        self._configs[tenant_id] = config

        _logger.debug(f"添加租户数据库引擎: {tenant_id}")

    def _evict_lru(self) -> None:
        """
        回收最近最少使用的引擎

        注意：此方法是同步的，不直接关闭引擎。
        引擎被移至待清理列表，在下次异步操作时清理。
        """
        if not self._engines:
            return

        # 获取最旧的 key
        tenant_id, engine = self._engines.popitem(last=False)
        _logger.info(f"回收租户数据库引擎: {tenant_id}")

        # 添加到待清理列表，在异步方法中统一关闭
        self._pending_dispose.append(engine)

        # 清理缓存
        self._session_factories.pop(tenant_id, None)
        self._access_times.pop(tenant_id, None)
        self._configs.pop(tenant_id, None)

    async def _cleanup_pending_dispose(self) -> None:
        """
        清理待释放的引擎

        在异步方法中调用，安全地关闭引擎。
        """
        if not self._pending_dispose:
            return

        for engine in self._pending_dispose:
            try:
                await engine.dispose()
            except Exception as e:
                _logger.warning(f"关闭引擎失败: {e}")

        self._pending_dispose.clear()

    async def release_idle(self, timeout: int | None = None) -> int:
        """
        释放空闲引擎

        Args:
            timeout: 空闲超时（秒），默认使用配置值

        Returns:
            int: 释放的引擎数量
        """
        # 先清理待释放的引擎
        await self._cleanup_pending_dispose()

        if timeout is None:
            timeout = self._idle_timeout

        now = datetime.now()
        threshold = now - timedelta(seconds=timeout)

        released = 0
        to_release = []

        for tenant_id, last_access in self._access_times.items():
            if last_access < threshold:
                to_release.append(tenant_id)

        for tenant_id in to_release:
            engine = self._engines.pop(tenant_id, None)
            if engine:
                await engine.dispose()
                self._session_factories.pop(tenant_id, None)
                self._access_times.pop(tenant_id, None)
                self._configs.pop(tenant_id, None)
                released += 1
                _logger.debug(f"释放空闲引擎: {tenant_id}")

        return released

    async def close(self) -> None:
        """
        关闭所有引擎
        """
        # 清理待释放的引擎
        await self._cleanup_pending_dispose()

        # 关闭默认引擎
        if self._default_engine:
            await self._default_engine.dispose()
            self._default_engine = None
            self._default_session_factory = None

        # 关闭所有租户引擎
        for tenant_id, engine in self._engines.items():
            try:
                await engine.dispose()
            except Exception as e:
                _logger.warning(f"关闭引擎失败: {tenant_id}, error={e}")

        self._engines.clear()
        self._session_factories.clear()
        self._access_times.clear()
        self._configs.clear()

        _logger.info("所有数据库引擎已关闭")

    def get_stats(self) -> dict:
        """
        获取引擎池统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "total_engines": len(self._engines),
            "max_engines": self._max_engines,
            "has_default": self._default_engine is not None,
            "tenants": list(self._engines.keys()),
        }


# 全局引擎池实例
_engine_pool: DatabaseEnginePool | None = None


def get_engine_pool() -> DatabaseEnginePool:
    """
    获取全局引擎池实例

    Returns:
        DatabaseEnginePool: 引擎池实例
    """
    global _engine_pool
    if _engine_pool is None:
        _engine_pool = DatabaseEnginePool()
    return _engine_pool


def init_default_engine(
    database_url: str,
    echo: bool = False,
    pool_size: int = DEFAULT_POOL_SIZE,
    max_overflow: int = DEFAULT_MAX_OVERFLOW,
) -> None:
    """
    初始化默认数据库引擎

    Args:
        database_url: 数据库连接 URL
        echo: 是否打印 SQL
        pool_size: 连接池大小
        max_overflow: 最大溢出连接数
    """
    pool = get_engine_pool()
    pool.init_default(database_url, echo, pool_size, max_overflow)


@asynccontextmanager
async def get_tenant_session(
    tenant_id: str | None = None,
    config: TenantDatabaseConfig | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """
    获取租户数据库会话

    Args:
        tenant_id: 租户 ID
        config: 租户数据库配置

    Yields:
        AsyncSession: 数据库会话
    """
    pool = get_engine_pool()
    async with pool.session(tenant_id, config) as session:
        yield session
