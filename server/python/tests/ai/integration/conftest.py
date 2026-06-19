"""
AI 模块集成测试配置

提供 ai 集成测试所需的 fixtures。
"""

import asyncio
import os
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"


# =============================================================================
# Event Loop (Session Scope)
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """创建 session 作用域的事件循环"""
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

    # conftest.py 在 server/python/tests/ai/integration/
    # 配置在 server/config/
    # 路径: conftest.py -> integration -> ai -> tests -> python -> server
    config_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "config"
    settings = init_settings(config_dir)

    return settings


# =============================================================================
# 数据库连接
# =============================================================================

@pytest_asyncio.fixture(scope="session")
async def ai_async_engine(integration_settings):
    """AI 模块异步数据库引擎"""
    engine = create_async_engine(
        url=integration_settings.sqlalchemy.url,
        echo=False,
        pool_pre_ping=True,
    )

    yield engine
    await engine.dispose()


# =============================================================================
# 测试数据 Fixtures
# =============================================================================

@pytest.fixture
def test_tenant_id():
    """测试租户 ID"""
    return "test-tenant-" + uuid.uuid4().hex[:8]


@pytest.fixture
def test_user_id():
    """测试用户 ID"""
    return "test-user-" + uuid.uuid4().hex[:8]


@pytest.fixture
def test_plugin_id():
    """测试插件 ID"""
    return "test-author/test-plugin"
