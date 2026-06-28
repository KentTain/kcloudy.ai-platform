"""
AI 模块集成测试配置

提供集成测试特有的 fixtures：
- 数据库引擎和会话

共享 fixtures（settings、tenant_id、API Key 等）来自上层 ai/conftest.py
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


# =============================================================================
# 数据库连接
# =============================================================================


@pytest_asyncio.fixture
async def ai_async_engine(ai_settings):
    """AI 模块异步数据库引擎（function 级别）"""
    engine = create_async_engine(
        url=ai_settings.sqlalchemy.url,
        echo=False,
        pool_pre_ping=True,
    )

    yield engine

    try:
        await engine.dispose()
    except Exception:
        pass


@pytest_asyncio.fixture
async def ai_async_session(ai_async_engine):
    """AI 模块异步数据库会话（function 级别）"""
    session = AsyncSession(bind=ai_async_engine, expire_on_commit=False)
    try:
        yield session
    finally:
        try:
            await session.rollback()
            await session.close()
        except Exception:
            pass
