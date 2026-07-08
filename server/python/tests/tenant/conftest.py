"""
Tenant 模块测试配置

提供 Tenant 模块的测试 fixtures：
- Mock 插件存储服务
- ModelScope API Token 配置
- ModelScope API 可用性检测
"""

import json
import os
import urllib.error
import urllib.request
from unittest.mock import AsyncMock, MagicMock

import pytest


# =============================================================================
# ModelScope API Token Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def modelscope_api_token():
    """
    获取 ModelScope API Token（session 级别）。

    优先从环境变量 E2E_MODELSCOPE_API_TOKEN 读取，如果未配置则使用默认测试配置。
    """
    return os.environ.get(
        "E2E_MODELSCOPE_API_TOKEN",
        "ms-902fa145-a02e-4ac4-97f8-e27737927984",
    )


# =============================================================================
# API Key 可用性检测（同步检测，与 ai conftest.py 模式一致）
# =============================================================================


@pytest.fixture(scope="session")
def modelscope_api_available(modelscope_api_token):
    """检测 ModelScope API Token 是否可用（session 级别，同步检测）"""
    try:
        # 测试 Skills API
        req = urllib.request.Request(
            "https://modelscope.cn/openapi/v1/skills?page_number=1&page_size=1",
            headers={
                "Authorization": f"Bearer {modelscope_api_token}",
                "Accept": "application/json",
            },
            method="GET",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("success", False)
            return False
    except urllib.error.HTTPError:
        return False
    except Exception:
        return False


# =============================================================================
# Mock Fixtures（单元测试使用）
# =============================================================================


@pytest.fixture
def mock_plugin_storage_service():
    """模拟插件存储服务"""
    mock_service = MagicMock()
    mock_service.upload_plugin_package = AsyncMock()
    mock_service.delete_plugin_package = AsyncMock(return_value=True)
    mock_service.delete_all_versions = AsyncMock(return_value=2)
    mock_service.package_exists = AsyncMock(return_value=True)
    mock_service.download_package = AsyncMock(return_value=b"fake package data")
    return mock_service
