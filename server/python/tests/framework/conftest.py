"""
Framework 模块测试配置

提供 framework 模块的集成测试 fixtures，支持：
- Redis 连接
- PostgreSQL 连接
- MinIO 连接
- 服务可用性检测
- 测试数据自动清理
"""

import asyncio
import os
import uuid
from pathlib import Path

import pytest
import pytest_asyncio

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"


# =============================================================================
# 配置加载
# =============================================================================

@pytest.fixture(scope="session")
def integration_settings():
    """
    加载集成测试配置

    使用 server/config/application-local.yml
    """
    from framework.configs import init_settings

    # conftest.py 在 server/python/tests/framework/
    # 配置在 server/config/
    config_dir = Path(__file__).parent.parent.parent.parent.parent / "config"
    settings = init_settings(config_dir)

    return settings


# =============================================================================
# 服务可用性检测
# =============================================================================

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


@pytest_asyncio.fixture(scope="session")
async def postgres_available(integration_settings):
    """检测 PostgreSQL 服务是否可用"""
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

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


@pytest.fixture(scope="session")
def minio_available(integration_settings):
    """检测 MinIO 服务是否可用"""
    try:
        from minio import Minio

        config = integration_settings.oss.minio
        client = Minio(
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
        )
        # 尝试列出 buckets 来验证连接
        list(client.list_buckets())
        return True
    except Exception:
        return False


# =============================================================================
# Redis Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="session")
async def redis_client(integration_settings, redis_available):
    """
    Redis 客户端 fixture（session 作用域）

    自动初始化和清理连接
    """
    if not redis_available:
        pytest.skip("Redis 服务不可用")

    from framework.cache.redis_util import RedisUtil

    await RedisUtil.init(integration_settings.redis)

    yield RedisUtil

    await RedisUtil.close()


@pytest.fixture
def redis_key_prefix():
    """生成唯一的 Redis 键前缀，用于测试隔离"""
    return f"test:{uuid.uuid4().hex}:"


@pytest_asyncio.fixture
async def redis_cleanup(redis_client, redis_key_prefix):
    """
    Redis 测试数据清理 fixture

    测试完成后自动清理带有前缀的键
    """
    yield redis_key_prefix

    # 清理测试数据
    keys = await redis_client.keys(f"{redis_key_prefix}*")
    if keys:
        for key in keys:
            await redis_client.delete(key)


# =============================================================================
# PostgreSQL Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="session")
async def postgres_engine(integration_settings, postgres_available):
    """
    PostgreSQL 引擎 fixture（session 作用域）
    """
    if not postgres_available:
        pytest.skip("PostgreSQL 服务不可用")

    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(
        integration_settings.sqlalchemy.url,
        echo=integration_settings.sqlalchemy.echo,
        pool_pre_ping=True,
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def postgres_session(postgres_engine):
    """
    PostgreSQL 会话 fixture

    每个测试使用独立会话，测试结束后回滚
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(bind=postgres_engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# =============================================================================
# MinIO Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="session")
async def minio_client(integration_settings, minio_available):
    """
    MinIO 客户端 fixture（session 作用域）
    """
    if not minio_available:
        pytest.skip("MinIO 服务不可用")

    from framework.storage.impl.minio import MinioStorage

    storage = MinioStorage(integration_settings.oss.minio)

    yield storage


@pytest.fixture
def minio_test_bucket():
    """生成唯一的测试存储桶名称"""
    return f"test-{uuid.uuid4().hex[:12]}"


@pytest_asyncio.fixture
async def minio_cleanup(minio_client, minio_test_bucket):
    """
    MinIO 测试数据清理 fixture

    测试完成后自动清理测试存储桶
    """
    # 确保测试存储桶存在
    await minio_client.create_bucket(minio_test_bucket)

    yield minio_test_bucket

    # 清理测试存储桶中的对象
    try:
        objects = await minio_client.list_objects(minio_test_bucket)
        for obj in objects:
            await minio_client.delete(minio_test_bucket, obj)
    except Exception:
        pass


# =============================================================================
# 工具函数
# =============================================================================

def unique_id() -> str:
    """生成唯一 ID"""
    return uuid.uuid4().hex


async def wait_for_condition(condition, timeout: float = 5.0, interval: float = 0.1):
    """
    等待条件满足

    Args:
        condition: 异步条件函数
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）
    """
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        if await condition():
            return True
        await asyncio.sleep(interval)
    return False
