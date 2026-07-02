"""
AI 模块测试配置

提供 AI 模块的测试 fixtures：
- AI 设置加载
- 数据库引擎和会话（集成测试）
- 测试数据生成（tenant_id、user_id）
- API Key 配置
- API Key 可用性检测
- Mock 数据 fixtures
"""

import json
import os
import shutil
import ssl
import urllib.error
import urllib.request
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# =============================================================================
# UV_PATH 环境变量设置
# =============================================================================

if not os.environ.get("UV_PATH"):
    uv_path = shutil.which("uv")
    if uv_path:
        os.environ["UV_PATH"] = uv_path

# =============================================================================
# AI 设置加载
# =============================================================================


@pytest.fixture(scope="session")
def ai_settings(integration_settings):
    """
    加载 AI 测试配置（session 级别）。

    复用根 conftest.py 的 integration_settings fixture。
    """
    return integration_settings


# =============================================================================
# 数据库 Fixtures（集成测试使用）
# =============================================================================


@pytest_asyncio.fixture
async def ai_async_engine(ai_settings, postgres_available):
    """
    AI 模块异步数据库引擎（function 级别）。

    用于 AI 模块的集成测试。
    """
    if not postgres_available:
        pytest.skip("PostgreSQL 服务不可用")

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
    """
    AI 模块异步数据库会话（function 级别）。
    """
    session = AsyncSession(bind=ai_async_engine, expire_on_commit=False)
    try:
        yield session
    finally:
        try:
            await session.rollback()
            await session.close()
        except Exception:
            pass


# =============================================================================
# 测试数据 Fixtures
# =============================================================================


@pytest.fixture
def test_tenant_id():
    """生成唯一测试租户 ID"""
    return "test-tenant-" + uuid.uuid4().hex[:8]


@pytest.fixture
def test_user_id():
    """生成唯一测试用户 ID"""
    return "test-user-" + uuid.uuid4().hex[:8]


# =============================================================================
# API Key Fixtures
# =============================================================================


@pytest.fixture
def tongyi_api_key():
    """
    获取通义千问 API Key。

    优先从环境变量 E2E_TONGYI_API_KEY 读取，如果未配置则使用默认测试配置。
    """
    return os.environ.get("E2E_TONGYI_API_KEY", "sk-623fdfb2b75f43b8bb6a61b8b183359a")


@pytest.fixture
def gpustack_api_key():
    """
    获取 GPUStack API Key。

    优先从环境变量 E2E_GPUSTACK_API_KEY 读取，如果未配置则使用默认测试配置。
    """
    return os.environ.get(
        "E2E_GPUSTACK_API_KEY",
        "gpustack_14d9f2aee5629a0f_465d73985f7b8f370caecd9e3de838ec",
    )


@pytest.fixture
def gpustack_endpoint():
    """
    获取 GPUStack Endpoint。

    优先从环境变量 E2E_GPUSTACK_ENDPOINT 读取，如果未配置则使用默认测试配置。
    """
    return os.environ.get("E2E_GPUSTACK_ENDPOINT", "https://llm-stack.flydiysz.cn")


# GPUStack 可用模型列表（从实际测试获取）
GPUSTACK_AVAILABLE_MODELS = [
    "qwen3.5-9b",  # 聊天模型
    "bge-large-zh-v1.5",  # Embedding 模型
    "bge-reranker-large",  # Reranker 模型
    "qwen3-embedding-0.6b",  # Embedding 模型
    "qwen3-reranker-0.6b",  # Reranker 模型
]


# =============================================================================
# API Key 可用性检测（同步检测，与基础设施检测模式一致）
# =============================================================================


@pytest.fixture(scope="session")
def tongyi_api_key_available(tongyi_api_key):
    """检测 tongyi API Key 是否可用（session 级别，同步检测）"""
    try:
        payload = json.dumps(
            {
                "model": "qwen-plus",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {tongyi_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except urllib.error.HTTPError:
        return False
    except Exception:
        return False


@pytest.fixture(scope="session")
def gpustack_api_key_available(gpustack_api_key, gpustack_endpoint):
    """检测 GPUStack API Key 是否可用（session 级别，同步检测）"""
    try:
        req = urllib.request.Request(
            f"{gpustack_endpoint}/v1/models",
            headers={"Authorization": f"Bearer {gpustack_api_key}"},
            method="GET",
        )

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return resp.status == 200
    except urllib.error.HTTPError:
        return False
    except Exception:
        return False


# =============================================================================
# Mock Fixtures（单元测试使用）
# =============================================================================


@pytest.fixture
def credential_schema():
    """标准凭证架构 fixture"""
    return [
        {
            "name": "api_key",
            "type": "secret-input",
            "required": True,
            "label": "API Key",
        },
        {
            "name": "api_secret",
            "type": "secret",
            "required": True,
            "label": "API Secret",
        },
        {
            "name": "endpoint",
            "type": "text-input",
            "required": False,
            "label": "Endpoint URL",
        },
        {
            "name": "model_type",
            "type": "select",
            "required": True,
            "options": [
                {"label": "GPT-4", "value": "gpt-4"},
                {"label": "GPT-3.5", "value": "gpt-3.5"},
            ],
        },
    ]


@pytest.fixture
def sample_plugin_config():
    """示例插件配置 fixture"""
    return {
        "version": "1.0.0",
        "type": "plugin",
        "name": "test-plugin",
        "tools_configuration": [
            {
                "provider": "test_provider",
                "credentials_schema": [
                    {
                        "name": "api_key",
                        "type": "secret-input",
                        "required": True,
                        "label": "API Key",
                    },
                ],
            }
        ],
    }


@pytest.fixture
def sample_credentials():
    """示例凭证数据 fixture"""
    return {
        "api_key": "sk-test-api-key-12345",
        "api_secret": "secret-value-67890",
        "endpoint": "https://api.example.com",
        "model_type": "gpt-4",
    }
