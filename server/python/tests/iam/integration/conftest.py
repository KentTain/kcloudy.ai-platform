"""
IAM 模块集成测试配置

提供 IAM 集成测试的 fixtures。
"""

import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"

# =============================================================================
# Windows 事件循环策略修复
# =============================================================================
if sys.platform == "win32":
    if hasattr(__import__('asyncio'), 'WindowsSelectorEventLoopPolicy'):
        __import__('asyncio').set_event_loop_policy(
            __import__('asyncio').WindowsSelectorEventLoopPolicy()
        )


# =============================================================================
# Event Loop
# =============================================================================
# 不再手动定义 event_loop，使用 pytest-asyncio 的自动管理
# pytest.ini 中配置了 asyncio_default_fixture_loop_scope = function
# 对于 session 作用域的异步 fixtures，使用 loop_scope 参数


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
# 服务可用性检测（同步检测，避免事件循环问题）
# =============================================================================

def _check_postgres_available(settings):
    """同步检测 PostgreSQL 服务是否可用"""
    import socket
    try:
        # 从 URL 中提取 host 和 port
        url = settings.sqlalchemy.url
        # postgresql+asyncpg://admin:password@host:port/database
        parts = url.split('@')[1].split('/')[0].split(':')
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 5432

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def _check_redis_available(settings):
    """同步检测 Redis 服务是否可用"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((
            settings.redis.single.host,
            settings.redis.single.port
        ))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture(scope="session")
def postgres_available(integration_settings):
    """检测 PostgreSQL 服务是否可用（同步检测）"""
    return _check_postgres_available(integration_settings)


@pytest.fixture(scope="session")
def redis_available(integration_settings):
    """检测 Redis 服务是否可用（同步检测）"""
    return _check_redis_available(integration_settings)


# =============================================================================
# 数据库引擎初始化（function 级别，使用独立引擎）
# =============================================================================

@pytest_asyncio.fixture
async def db_engine(integration_settings, postgres_available):
    """初始化数据库引擎（function 级别，使用独立引擎避免全局状态问题）"""
    if not postgres_available:
        pytest.skip("PostgreSQL 服务不可用")

    # 创建独立的引擎实例，不使用全局引擎
    engine = create_async_engine(
        integration_settings.sqlalchemy.url,
        echo=integration_settings.sqlalchemy.echo,
        pool_pre_ping=True,
    )

    yield engine

    # 安全清理
    try:
        await engine.dispose()
    except Exception:
        pass


@pytest_asyncio.fixture
async def init_redis(integration_settings, redis_available):
    """初始化 Redis（function 级别）"""
    if not redis_available:
        pytest.skip("Redis 服务不可用")

    from framework.cache.redis_util import RedisUtil

    # 如果已初始化，先关闭
    if RedisUtil.is_initialized():
        try:
            await RedisUtil.close()
        except Exception:
            pass

    await RedisUtil.init(integration_settings.redis)

    yield

    # 安全关闭连接
    try:
        await RedisUtil.close()
    except Exception:
        pass


# =============================================================================
# 测试数据 Fixtures
# =============================================================================

TEST_TENANT_ID = "00000000-0000-0000-0000-000000000001"
TEST_TENANT_CODE = "TEST_TENANT"


@pytest.fixture(scope="session")
def test_tenant_id():
    """获取测试租户 ID（session 级别，返回固定值）"""
    return TEST_TENANT_ID


@pytest.fixture
def cleanup_users():
    """清理测试创建的用户（仅收集 ID，实际清理由测试后处理）"""
    created_user_ids = []
    yield created_user_ids
    # 不在这里清理，避免事件循环问题


# =============================================================================
# Session Fixture
# =============================================================================

@pytest_asyncio.fixture
async def session(db_engine):
    """数据库会话 fixture（function 级别）"""
    session = AsyncSession(bind=db_engine)
    try:
        yield session
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            await session.close()
        except RuntimeError:
            pass  # 事件循环已关闭
