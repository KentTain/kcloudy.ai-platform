"""
数据库引擎和会话配置（代理模式）

参照 Alon 项目 alon.models.core.engine 实现
"""

from loguru import logger
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from demo.configs.settings import settings

_logger = logger.bind(name=__name__)

# 全局引擎实例（由 setup_orm 初始化）
engine_instance: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """获取数据库引擎实例

    Returns:
        AsyncEngine: 数据库引擎

    Raises:
        RuntimeError: 引擎未初始化时抛出
    """
    global engine_instance
    if engine_instance is None:
        raise RuntimeError("数据库引擎未初始化，请先调用 setup_orm()")
    return engine_instance


def create_engine() -> AsyncEngine:
    """创建异步数据库引擎

    Returns:
        AsyncEngine: 配置好的异步数据库引擎
    """
    engine_config: dict = {
        "url": settings.sqlalchemy.database_url,
        "echo": settings.sqlalchemy.echo,
    }

    # 连接池配置
    pool_size = settings.sqlalchemy.pool_size
    max_overflow = settings.sqlalchemy.max_overflow

    engine_config.update(
        {
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_pre_ping": True,
        }
    )

    _logger.debug(f"连接池配置 - 大小: {pool_size}, 最大溢出: {max_overflow}")

    return create_async_engine(**engine_config)


def setup_connection_events(engine: AsyncEngine) -> None:
    """设置连接事件监听器"""

    @event.listens_for(engine.sync_engine, "connect")
    def on_connect(dbapi_connection, connection_record):
        """在每次连接数据库时触发"""
        try:
            if hasattr(dbapi_connection, "set_client_encoding"):
                dbapi_connection.set_client_encoding("UTF8")
        except Exception:
            _logger.exception("连接池连接事件处理失败")


def setup_orm() -> None:
    """初始化 ORM 引擎

    在应用启动时调用此函数初始化数据库引擎。
    """
    global engine_instance

    if engine_instance is not None:
        _logger.warning("数据库引擎已初始化，跳过重复初始化")
        return

    engine_instance = create_engine()
    setup_connection_events(engine_instance)
    _logger.info("数据库引擎初始化完成")


class _EngineProxy:
    """引擎代理类，支持延迟初始化"""

    def __getattr__(self, name):
        """访问引擎的属性和方法"""
        return getattr(get_engine(), name)


engine = _EngineProxy()
"""异步数据库引擎（代理模式）"""


class _SessionMakerProxy:
    """会话工厂代理类"""

    def __call__(self, *args, **kwargs):
        """创建新的数据库会话"""
        session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
        return session_factory(*args, **kwargs)


async_session = _SessionMakerProxy()
"""异步会话工厂"""

# 向后兼容别名
async_session_factory = async_session
"""异步会话工厂（向后兼容别名）"""
