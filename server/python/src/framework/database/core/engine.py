"""
数据库引擎管理

提供数据库引擎和会话管理，支持从配置自动初始化。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from loguru import logger
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from framework.utils.log_util import write_error, write_info, write_warning

_logger = logger.bind(name=__name__)


class EngineManager:
    """数据库引擎管理器（单例模式）"""

    _instance: "EngineManager | None" = None
    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None

    def __new__(cls) -> "EngineManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 30,
        **kwargs,
    ) -> None:
        """
        初始化数据库引擎

        Args:
            database_url: 数据库连接 URL
            echo: 是否打印 SQL
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            **kwargs: 额外配置参数
        """
        if self._engine is not None:
            write_warning("数据库引擎已初始化，跳过重复初始化")
            return

        engine_config = {
            "url": database_url,
            "echo": echo,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_pre_ping": True,
            **kwargs,
        }

        self._engine = create_async_engine(**engine_config)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self._setup_connection_events()
        write_info(f"连接池配置 - 大小: {pool_size}, 最大溢出: {max_overflow}")
        write_info("数据库引擎初始化完成")

    def _setup_connection_events(self) -> None:
        """设置连接事件监听器"""
        if self._engine is None:
            return

        @event.listens_for(self._engine.sync_engine, "connect")
        def on_connect(dbapi_connection, _connection_record):
            """在每次连接数据库时触发"""
            try:
                if hasattr(dbapi_connection, "set_client_encoding"):
                    dbapi_connection.set_client_encoding("UTF8")
            except Exception as e:
                _logger.exception(f"连接池连接事件处理失败，失败消息：{e}")
                write_error("连接池连接事件处理失败")

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话

        Yields:
            AsyncSession: 数据库会话
        """
        if self._session_factory is None:
            raise RuntimeError("数据库引擎未初始化，请先调用 init()")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @property
    def engine(self) -> AsyncEngine:
        """获取数据库引擎"""
        if self._engine is None:
            raise RuntimeError("数据库引擎未初始化")
        return self._engine

    def create_session(self) -> AsyncSession:
        """创建新的数据库会话"""
        if self._session_factory is None:
            raise RuntimeError("数据库引擎未初始化")
        return self._session_factory()


# 全局引擎管理器实例
_engine_manager = EngineManager()


def get_engine() -> AsyncEngine:
    """获取数据库引擎"""
    return _engine_manager.engine


def setup_engine(
    database_url: str,
    echo: bool = False,
    pool_size: int = 20,
    max_overflow: int = 30,
    **kwargs,
) -> None:
    """
    初始化数据库引擎

    Args:
        database_url: 数据库连接 URL
        echo: 是否打印 SQL
        pool_size: 连接池大小
        max_overflow: 最大溢出连接数
        **kwargs: 额外配置参数
    """
    _engine_manager.init(
        database_url=database_url,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
        **kwargs,
    )


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with _engine_manager.session() as session:
        yield session


def create_session() -> AsyncSession:
    """创建新的数据库会话"""
    return _engine_manager.create_session()


class _SessionProxy:
    """
    会话代理类（多租户感知）

    .. deprecated::
        此代理已废弃，将在未来版本移除。请使用以下替代方案：

        - Controller: 使用 ``session: AsyncSession = Depends(get_db_session)``
        - Listener: 使用 ``async with get_listener_session() as session:``
        - Task: 使用 ``async with get_task_session() as session:``
        - Service: 接收 ``session: AsyncSession`` 参数

    此代理保持向后兼容，内部使用 DatabaseEnginePool 实现多租户支持。
    """

    @asynccontextmanager
    async def __call__(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话（多租户感知）

        自动根据 TenantContext 选择正确的数据库引擎：
        - 逻辑隔离：使用默认引擎，通过 tenant_id 字段过滤
        - 物理隔离：使用租户专属引擎

        Yields:
            AsyncSession: 数据库会话
        """
        from framework.database.core.engine_pool import get_engine_pool
        from framework.tenant.context import TenantContext

        tenant_id = TenantContext.get_tenant_id()
        db_config = TenantContext.get_database_config()

        pool = get_engine_pool()
        async with pool.session(tenant_id, db_config) as session:
            try:
                yield session
            except Exception:
                raise


async_session = _SessionProxy()
"""
异步会话工厂（代理模式，多租户感知）

.. deprecated::
    已废弃，请使用依赖注入模式。
    - Controller: 使用 Depends(get_db_session)
    - Listener: 使用 get_listener_session()
    - Task: 使用 get_task_session()
"""
