"""
数据库引擎管理

提供数据库引擎和会话管理。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class EngineManager:
    """数据库引擎管理器"""

    _instance: "EngineManager | None" = None
    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None

    def __new__(cls) -> "EngineManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init(self, database_url: str, **kwargs) -> None:
        """
        初始化数据库引擎

        Args:
            database_url: 数据库连接 URL
            **kwargs: 额外配置参数
        """
        self._engine = create_async_engine(database_url, **kwargs)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

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
            raise RuntimeError("数据库引擎未初始化")

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


def get_engine() -> AsyncEngine:
    """获取数据库引擎"""
    return EngineManager().engine


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with EngineManager().session() as session:
        yield session
