"""
AI 模块测试公共配置

提供所有测试类型（unit/integration/e2e）共享的 fixtures：
- 环境变量设置
- Windows 事件循环策略修复
- 配置加载
- 测试数据生成（tenant_id、user_id）
- API Key 配置
- mock 数据 fixtures
"""

import os
import sys
import uuid
from pathlib import Path

from unittest.mock import AsyncMock

import pytest

# =============================================================================
# 环境变量设置
# =============================================================================
os.environ.setdefault("PYTHON_SERVICE_ENV", "local")
os.environ.setdefault("TZ", "Asia/Shanghai")

# 设置 UV_PATH（如果未设置）
if not os.environ.get("UV_PATH"):
    import shutil

    uv_path = shutil.which("uv")
    if uv_path:
        os.environ["UV_PATH"] = uv_path

# =============================================================================
# Windows 事件循环策略修复
# 注意：不在此处全局设置事件循环策略，由各子目录 conftest.py 按需设置
# - integration 测试：使用 SelectorEventLoop（asyncpg 兼容性更好）
# - e2e 测试：使用 ProactorEventLoop（支持子进程如 uv 命令）
# =============================================================================


# =============================================================================
# 配置加载
# =============================================================================

# 配置目录（相对于 server/python/tests/ai/）
_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "config"


def _load_settings():
    """加载测试配置"""
    from framework.configs import init_settings

    return init_settings(_CONFIG_DIR)


@pytest.fixture(scope="session")
def ai_settings():
    """加载 AI 测试配置（session 级别）"""
    return _load_settings()


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
    return os.environ.get(
        "E2E_TONGYI_API_KEY", "sk-623fdfb2b75f43b8bb6a61b8b183359a"
    )


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
    return os.environ.get(
        "E2E_GPUSTACK_ENDPOINT", "https://llm-stack.flydiysz.cn"
    )


# GPUStack 可用模型列表（从实际测试获取）
GPUSTACK_AVAILABLE_MODELS = [
    "qwen3.5-9b",              # 聊天模型
    "bge-large-zh-v1.5",       # Embedding 模型
    "bge-reranker-large",      # Reranker 模型
    "qwen3-embedding-0.6b",    # Embedding 模型
    "qwen3-reranker-0.6b",     # Reranker 模型
]


# =============================================================================
# Mock Fixtures（单元测试使用）
# =============================================================================


@pytest.fixture
def session():
    """异步数据库会话 mock fixture"""
    return AsyncMock()


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
