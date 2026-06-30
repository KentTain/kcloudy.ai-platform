"""
默认模型管理 API 集成测试

测试默认模型的 CRUD 操作和模型列表 API 的图标字段。
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.plugin_default_model import PluginDefaultModel


@pytest.fixture
async def tenant_headers():
    """获取租户管理员认证头"""
    # TODO: 根据实际认证机制调整
    return {
        "Authorization": "Bearer test_token",
        "X-Tenant-ID": "test_tenant",
    }


@pytest.mark.asyncio
class TestDefaultModelAPI:
    """默认模型 API 测试"""

    async def test_get_default_model_not_found(self, tenant_headers: dict):
        """测试获取不存在的默认模型"""
        async with AsyncClient(base_url="http://localhost:8080") as client:
            response = await client.get(
                "/ai/console/v1/plugins/default-models",
                params={"model_type": "llm"},
                headers=tenant_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"] is None

    async def test_set_and_get_default_model(self, tenant_headers: dict):
        """测试设置和获取默认模型"""
        # 1. 设置默认模型
        async with AsyncClient(base_url="http://localhost:8080") as client:
            response = await client.post(
                "/ai/console/v1/plugins/default-models",
                json={
                    "model_type": "llm",
                    "plugin_id": "openai",
                    "model_name": "gpt-4o-mini",
                },
                headers=tenant_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["model_type"] == "llm"
        assert data["data"]["plugin_id"] == "openai"
        assert data["data"]["model_name"] == "gpt-4o-mini"

        default_model_id = data["data"]["id"]

        # 2. 获取默认模型
        async with AsyncClient(base_url="http://localhost:8080") as client:
            response = await client.get(
                "/ai/console/v1/plugins/default-models",
                params={"model_type": "llm"},
                headers=tenant_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == default_model_id
        assert data["data"]["model_type"] == "llm"
        assert data["data"]["plugin_id"] == "openai"

    async def test_update_default_model(self, tenant_headers: dict):
        """测试更新默认模型"""
        # 1. 设置默认模型
        async with AsyncClient(base_url="http://localhost:8080") as client:
            await client.post(
                "/ai/console/v1/plugins/default-models",
                json={
                    "model_type": "llm",
                    "plugin_id": "openai",
                    "model_name": "gpt-4o-mini",
                },
                headers=tenant_headers,
            )

        # 2. 更新默认模型
        async with AsyncClient(base_url="http://localhost:8080") as client:
            response = await client.post(
                "/ai/console/v1/plugins/default-models",
                json={
                    "model_type": "llm",
                    "plugin_id": "anthropic",
                    "model_name": "claude-3-5-sonnet-20241022",
                },
                headers=tenant_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["plugin_id"] == "anthropic"
        assert data["data"]["model_name"] == "claude-3-5-sonnet-20241022"

        # 3. 验证更新
        async with AsyncClient(base_url="http://localhost:8080") as client:
            response = await client.get(
                "/ai/console/v1/plugins/default-models",
                params={"model_type": "llm"},
                headers=tenant_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["plugin_id"] == "anthropic"

    async def test_set_default_model_with_credential(
        self, tenant_headers: dict
    ):
        """测试设置带凭证的默认模型"""
        async with AsyncClient(base_url="http://localhost:8080") as client:
            response = await client.post(
                "/ai/console/v1/plugins/default-models",
                json={
                    "model_type": "llm",
                    "plugin_id": "openai",
                    "model_name": "gpt-4o",
                    "credential_id": "cred_123",
                    "custom_base_url": "https://api.openai.com/v1",
                },
                headers=tenant_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["credential_id"] == "cred_123"
        assert data["data"]["custom_base_url"] == "https://api.openai.com/v1"


@pytest.mark.asyncio
class TestModelListAPI:
    """模型列表 API 测试"""

    async def test_get_models_with_icon_fields(self, tenant_headers: dict):
        """测试获取模型列表（包含图标字段）"""
        async with AsyncClient(base_url="http://localhost:8080") as client:
            response = await client.get(
                "/ai/console/v1/models",
                headers=tenant_headers,
            )

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "providers" in data
        assert isinstance(data["providers"], list)

        # 如果有提供商，验证图标字段
        if data["providers"]:
            provider = data["providers"][0]
            assert "id" in provider
            assert "name" in provider
            assert "models" in provider

            # 验证新增的图标字段（可选）
            assert "icon_small" in provider or provider.get("icon_small") is None
            assert "icon_large" in provider or provider.get("icon_large") is None

            # 如果有模型，验证模型结构
            if provider["models"]:
                model = provider["models"][0]
                assert "id" in model
                assert "name" in model

    async def test_models_response_format(self, tenant_headers: dict):
        """测试模型列表响应格式符合预期"""
        async with AsyncClient(base_url="http://localhost:8080") as client:
            response = await client.get(
                "/ai/console/v1/models",
                headers=tenant_headers,
            )

        assert response.status_code == 200
        data = response.json()

        # 验证提供商数据结构
        for provider in data.get("providers", []):
            # 验证模型 ID 格式为 provider/model
            for model in provider.get("models", []):
                assert "/" in model["id"], f"Model ID should contain '/': {model['id']}"
                parts = model["id"].split("/")
                assert len(parts) == 2, f"Model ID format should be 'provider/model': {model['id']}"


@pytest.mark.asyncio
class TestDefaultModelIntegration:
    """默认模型集成测试"""

    async def test_default_model_persistence(self, tenant_headers: dict):
        """测试默认模型持久化"""
        # 1. 设置默认模型
        async with AsyncClient(base_url="http://localhost:8080") as client:
            await client.post(
                "/ai/console/v1/plugins/default-models",
                json={
                    "model_type": "text-embedding",
                    "plugin_id": "openai",
                    "model_name": "text-embedding-3-small",
                },
                headers=tenant_headers,
            )

        # 2. 重新获取，验证持久化
        async with AsyncClient(base_url="http://localhost:8080") as client:
            response = await client.get(
                "/ai/console/v1/plugins/default-models",
                params={"model_type": "text-embedding"},
                headers=tenant_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"] is not None
        assert data["data"]["model_type"] == "text-embedding"
        assert data["data"]["model_name"] == "text-embedding-3-small"

    async def test_multiple_model_types(self, tenant_headers: dict):
        """测试多种模型类型的默认模型"""
        model_types = ["llm", "text-embedding", "rerank"]

        for model_type in model_types:
            async with AsyncClient(base_url="http://localhost:8080") as client:
                response = await client.post(
                    "/ai/console/v1/plugins/default-models",
                    json={
                        "model_type": model_type,
                        "plugin_id": "test_provider",
                        "model_name": f"test_model_{model_type}",
                    },
                    headers=tenant_headers,
                )

            assert response.status_code == 200, f"Failed to set default model for {model_type}"

        # 验证每种类型都有独立的默认模型
        for model_type in model_types:
            async with AsyncClient(base_url="http://localhost:8080") as client:
                response = await client.get(
                    "/ai/console/v1/plugins/default-models",
                    params={"model_type": model_type},
                    headers=tenant_headers,
                )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["model_type"] == model_type
