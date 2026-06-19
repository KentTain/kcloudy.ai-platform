"""
Demo 集成测试配置

提供 demo 集成测试所需的 fixtures。
"""

import os
import uuid
from pathlib import Path

import pytest
import pytest_asyncio

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"


# =============================================================================
# Event Loop (Session Scope)
# =============================================================================

# 注意：session 作用域的异步 fixtures 需要手动定义 event_loop

@pytest.fixture(scope="session")
def event_loop():
    """创建 session 作用域的事件循环"""
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


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

    # conftest.py 在 server/python/tests/demo/integration/
    # 配置在 server/config/
    # 路径: conftest.py -> integration -> demo -> tests -> python -> server
    config_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "config"
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
