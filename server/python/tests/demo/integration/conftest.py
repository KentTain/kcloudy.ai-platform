"""
Demo 集成测试配置

提供 demo 集成测试所需的 fixtures。
"""

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
if sys.platform == "win32":
    if hasattr(__import__('asyncio'), 'WindowsSelectorEventLoopPolicy'):
        __import__('asyncio').set_event_loop_policy(
            __import__('asyncio').WindowsSelectorEventLoopPolicy()
        )


# =============================================================================
# 配置加载
# =============================================================================

@pytest.fixture(scope="session")
def integration_settings():
    """加载集成测试配置"""
    from framework.configs import init_settings

    config_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "config"
    settings = init_settings(config_dir)

    return settings


# =============================================================================
# 服务可用性检测（同步检测）
# =============================================================================

@pytest.fixture(scope="session")
def redis_available(integration_settings):
    """检测 Redis 服务是否可用（同步检测）"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((
            integration_settings.redis.single.host,
            integration_settings.redis.single.port
        ))
        sock.close()
        return result == 0
    except Exception:
        return False


# =============================================================================
# Redis Fixtures（function 级别）
# =============================================================================

@pytest_asyncio.fixture
async def redis_client(integration_settings, redis_available):
    """
    Redis 客户端 fixture（function 级别）

    每个测试获取独立的 Redis 连接，避免事件循环冲突。
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
