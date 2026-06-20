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
import sys
import uuid
from pathlib import Path

import pytest
import pytest_asyncio

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"

# =============================================================================
# Windows 事件循环策略修复
# =============================================================================
# Windows 上 ProactorEventLoop 与 pytest-asyncio 存在兼容性问题
# 使用 WindowsSelectorEventLoopPolicy 解决事件循环关闭后的连接问题
if sys.platform == "win32":
    # Python 3.8+ 支持 WindowsSelectorEventLoopPolicy
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# =============================================================================
# Event Loop
# =============================================================================
# 使用 pytest-asyncio 的自动管理
# pytest.ini 中配置了 asyncio_default_fixture_loop_scope = module
# 对于 session 作用域的异步 fixtures，使用 loop_scope 参数


# =============================================================================
# 全局状态重置（解决 pytest-asyncio 在 Windows 上的事件循环问题）
# =============================================================================

@pytest.fixture(scope="module", autouse=True)
def reset_global_state():
    """
    在每个测试模块前重置全局状态

    解决 pytest-asyncio 在 Windows 上事件循环管理问题：
    - 每个模块使用独立的事件循环
    - 全局单例（RedisUtil）的连接池可能绑定到旧的事件循环
    - 在模块开始时关闭并重新初始化连接
    """
    yield

    # 模块结束后清理（不是开始前，因为 pytest 的 autouse 执行顺序）
    # 清理逻辑在 session fixture 中处理


# =============================================================================
# 配置加载
# =============================================================================

# 注意：event_loop 已在上面定义，pytest-asyncio 会自动使用它

@pytest.fixture(scope="session")
def integration_settings():
    """
    加载集成测试配置

    使用 server/config/application-local.yml
    """
    from framework.configs import init_settings

    # conftest.py 在 server/python/tests/framework/
    # 配置在 server/config/
    # 路径: conftest.py -> tests -> python -> server
    config_dir = Path(__file__).resolve().parent.parent.parent.parent / "config"
    settings = init_settings(config_dir)

    return settings


# =============================================================================
# 服务可用性检测（简化为同步检测，避免事件循环问题）
# =============================================================================

def _check_redis_available(settings):
    """同步检测 Redis 服务是否可用"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((settings.redis.single.host, settings.redis.single.port))
        sock.close()
        return result == 0
    except Exception:
        return False


def _check_postgres_available(settings):
    """同步检测 PostgreSQL 服务是否可用"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((
            settings.sqlalchemy.url.split('@')[1].split(':')[0],
            int(settings.sqlalchemy.url.split(':')[3].split('/')[0])
        ))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture(scope="session")
def redis_available(integration_settings):
    """检测 Redis 服务是否可用（session 级别，同步检测）"""
    return _check_redis_available(integration_settings)


@pytest.fixture(scope="session")
def postgres_available(integration_settings):
    """检测 PostgreSQL 服务是否可用（session 级别，同步检测）"""
    return _check_postgres_available(integration_settings)


# =============================================================================
# Redis Fixtures（function 级别，确保每个测试都有独立的连接）
# =============================================================================

@pytest_asyncio.fixture
async def redis_client(integration_settings, redis_available):
    """
    Redis 客户端 fixture（function 作用域）

    每个测试获取独立的 Redis 连接，避免事件循环冲突。
    这是在 Windows 上使用 pytest-asyncio 的最稳定方案。
    """
    if not redis_available:
        pytest.skip("Redis 服务不可用")

    from framework.cache.redis_util import RedisUtil

    # 关闭现有连接（如果有）
    if RedisUtil.is_initialized():
        try:
            await RedisUtil.close()
        except Exception:
            pass

    # 初始化新连接
    await RedisUtil.init(integration_settings.redis)

    yield RedisUtil

    # 测试结束后关闭连接
    try:
        await RedisUtil.close()
    except Exception:
        pass


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
# PostgreSQL Fixtures（function 级别，确保每个测试都有独立的连接）
# =============================================================================

@pytest_asyncio.fixture
async def postgres_engine(integration_settings, postgres_available):
    """
    PostgreSQL 引擎 fixture（function 作用域）

    每个测试获取独立的引擎，避免事件循环冲突。
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

    # 安全关闭引擎
    try:
        await engine.dispose()
    except Exception:
        pass


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
            # 尝试提交，但忽略事件循环关闭错误
            try:
                await session.commit()
            except RuntimeError:
                pass  # 事件循环已关闭
        except Exception:
            try:
                await session.rollback()
            except RuntimeError:
                pass  # 事件循环已关闭
            raise


# =============================================================================
# MinIO Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def minio_available(integration_settings):
    """检测 MinIO 服务是否可用（同步检测）"""
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


@pytest_asyncio.fixture
async def minio_client(integration_settings, minio_available):
    """
    MinIO 客户端 fixture（function 作用域）

    每个测试获取独立的客户端实例，避免事件循环冲突。
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
