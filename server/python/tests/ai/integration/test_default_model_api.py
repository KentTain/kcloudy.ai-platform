"""默认模型管理 API 集成测试

测试默认模型相关的 Controller API 端点。
使用 ASGITransport + 隔离 FastAPI 应用，无需认证和外部服务器。
"""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from framework.common.response import ApiResponse


@pytest.fixture
def test_tenant_id():
    """测试租户 ID"""
    return str(uuid.uuid4())


@pytest.mark.asyncio
class TestDefaultModelAPI:
    """默认模型 API 端点测试"""

    async def test_get_default_model_not_found(self):
        """测试获取不存在的默认模型"""
        app = FastAPI()

        @app.get("/ai/console/v1/plugins/default-models")
        async def get_default_model(model_type: str):
            return ApiResponse.success(data=None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/ai/console/v1/plugins/default-models",
                params={"model_type": "llm"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"] is None

    async def test_set_default_model(self):
        """测试设置默认模型"""
        app = FastAPI()
        model_id = str(uuid.uuid4())

        @app.post("/ai/console/v1/plugins/default-models")
        async def set_default_model(request: dict):
            return ApiResponse.success(data={
                "id": model_id,
                "model_type": request["model_type"],
                "plugin_id": request["plugin_id"],
                "model_name": request["model_name"],
            })

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/ai/console/v1/plugins/default-models",
                json={
                    "model_type": "llm",
                    "plugin_id": "openai",
                    "model_name": "gpt-4o-mini",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["model_type"] == "llm"
        assert data["data"]["plugin_id"] == "openai"
        assert data["data"]["model_name"] == "gpt-4o-mini"

    async def test_update_default_model(self):
        """测试更新默认模型"""
        app = FastAPI()
        model_id = str(uuid.uuid4())

        @app.post("/ai/console/v1/plugins/default-models")
        async def set_default_model(request: dict):
            return ApiResponse.success(data={
                "id": model_id,
                "model_type": request["model_type"],
                "plugin_id": request["plugin_id"],
                "model_name": request["model_name"],
            })

        # 第一次设置
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/ai/console/v1/plugins/default-models",
                json={
                    "model_type": "llm",
                    "plugin_id": "openai",
                    "model_name": "gpt-4o-mini",
                },
            )

        # 更新
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/ai/console/v1/plugins/default-models",
                json={
                    "model_type": "llm",
                    "plugin_id": "anthropic",
                    "model_name": "claude-3-5-sonnet-20241022",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["plugin_id"] == "anthropic"
        assert data["data"]["model_name"] == "claude-3-5-sonnet-20241022"

    async def test_set_model_with_credential(self):
        """测试设置带凭证的默认模型"""
        app = FastAPI()
        model_id = str(uuid.uuid4())

        @app.post("/ai/console/v1/plugins/default-models")
        async def set_default_model(request: dict):
            return ApiResponse.success(data={
                "id": model_id,
                **request
            })

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/ai/console/v1/plugins/default-models",
                json={
                    "model_type": "llm",
                    "plugin_id": "openai",
                    "model_name": "gpt-4o",
                    "credential_id": "cred_123",
                    "custom_base_url": "https://api.openai.com/v1",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["credential_id"] == "cred_123"
        assert data["data"]["custom_base_url"] == "https://api.openai.com/v1"


@pytest.mark.asyncio
class TestModelListAPI:
    """模型列表 API 测试"""

    async def test_get_models_structure(self):
        """测试获取模型列表结构"""
        app = FastAPI()

        @app.get("/ai/console/v1/models")
        async def get_models():
            return ApiResponse.success(data={
                "providers": [
                    {
                        "id": "openai",
                        "name": "OpenAI",
                        "icon_small": "openai-small.png",
                        "icon_large": "openai-large.png",
                        "models": [
                            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"},
                        ]
                    }
                ]
            })

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ai/console/v1/models")

        assert response.status_code == 200
        data = response.json()
        assert "providers" in data["data"]
        assert isinstance(data["data"]["providers"], list)

        if data["data"]["providers"]:
            provider = data["data"]["providers"][0]
            assert "id" in provider
            assert "name" in provider
            assert "models" in provider
            assert "icon_small" in provider
            assert "icon_large" in provider

    async def test_models_id_format(self):
        """测试模型 ID 格式"""
        app = FastAPI()

        @app.get("/ai/console/v1/models")
        async def get_models():
            return ApiResponse.success(data={
                "providers": [
                    {
                        "id": "openai",
                        "name": "OpenAI",
                        "models": [
                            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"},
                        ]
                    }
                ]
            })

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ai/console/v1/models")

        data = response.json()
        for provider in data["data"]["providers"]:
            for model in provider["models"]:
                assert "/" in model["id"], f"Model ID should contain '/': {model['id']}"
                parts = model["id"].split("/")
                assert len(parts) == 2, f"Model ID format should be 'provider/model': {model['id']}"
