"""
IAM 模块集成测试配置

提供 IAM 集成测试的 fixtures。
"""

import os
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"


# =============================================================================
# Event Loop (Session Scope)
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """创建 session 作用域的事件循环"""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# 配置加载
# =============================================================================

@pytest.fixture(scope="session")
def integration_settings():
    """加载集成测试配置"""
    from framework.configs import init_settings

    # conftest.py 在 server/python/tests/iam/integration/
    # 配置在 server/config/
    # 路径: conftest.py -> integration -> iam -> tests -> python -> server
    config_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "config"
    settings = init_settings(config_dir)
    return settings


# =============================================================================
# 服务可用性检测
# =============================================================================

@pytest_asyncio.fixture(scope="session")
async def postgres_available(integration_settings):
    """检测 PostgreSQL 服务是否可用"""
    try:
        engine = create_async_engine(
            integration_settings.sqlalchemy.url,
            echo=False
        )
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception:
        return False


@pytest_asyncio.fixture(scope="session")
async def redis_available(integration_settings):
    """检测 Redis 服务是否可用"""
    from framework.cache.redis_util import RedisUtil

    try:
        await RedisUtil.init(integration_settings.redis)
        result = await RedisUtil.health_check()
        await RedisUtil.close()
        return result
    except Exception:
        return False


# =============================================================================
# 数据库引擎初始化
# =============================================================================

@pytest_asyncio.fixture(scope="session")
async def db_engine(integration_settings, postgres_available):
    """初始化数据库引擎"""
    if not postgres_available:
        pytest.skip("PostgreSQL 服务不可用")

    from framework.database.core.engine import get_engine, setup_engine

    # 初始化全局引擎
    setup_engine(
        database_url=integration_settings.sqlalchemy.url,
        echo=integration_settings.sqlalchemy.echo,
    )
    engine = get_engine()

    yield engine

    # 清理
    from framework.database.core.engine import _engine_manager
    await _engine_manager.close()


@pytest_asyncio.fixture(scope="session")
async def init_redis(integration_settings, redis_available):
    """初始化 Redis"""
    if not redis_available:
        pytest.skip("Redis 服务不可用")

    from framework.cache.redis_util import RedisUtil
    await RedisUtil.init(integration_settings.redis)

    yield

    await RedisUtil.close()


# =============================================================================
# 测试数据 Fixtures
# =============================================================================

TEST_TENANT_ID = "00000000-0000-0000-0000-000000000001"
TEST_TENANT_CODE = "TEST_TENANT"


@pytest_asyncio.fixture(scope="session")
async def test_tenant(db_engine):
    """创建或获取测试租户"""

    from tenant.models import Tenant, TenantStatus

    async with AsyncSession(bind=db_engine) as session:
        # 检查租户是否存在
        stmt = select(Tenant).where(Tenant.id == TEST_TENANT_ID)
        result = await session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is None:
            # 创建测试租户
            tenant = Tenant(
                id=TEST_TENANT_ID,
                name="测试租户",
                code=TEST_TENANT_CODE,
                status=TenantStatus.ACTIVE,
            )
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)

    yield TEST_TENANT_ID

    # 清理：不删除测试租户，因为可能被其他测试使用


@pytest.fixture
def test_tenant_id(test_tenant):
    """获取测试租户 ID"""
    return test_tenant


@pytest_asyncio.fixture
async def cleanup_users(db_engine):
    """清理测试创建的用户"""
    created_user_ids = []

    yield created_user_ids

    # 清理测试数据
    if created_user_ids:
        from sqlalchemy import delete

        from iam.models import User

        async with AsyncSession(bind=db_engine) as session:
            await session.execute(
                delete(User).where(User.id.in_(created_user_ids))
            )
            await session.commit()


# =============================================================================
# Session Fixture
# =============================================================================

@pytest_asyncio.fixture
async def session(db_engine):
    """数据库会话 fixture"""
    async with AsyncSession(bind=db_engine) as session:
        yield session
