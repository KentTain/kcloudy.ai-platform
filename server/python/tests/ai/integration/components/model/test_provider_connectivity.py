# Provider API 连通性集成测试

import os

import httpx
import pytest


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def tongyi_api_key():
    """获取通义千问 API Key"""
    return os.environ.get(
        "E2E_TONGYI_API_KEY", "sk-623fdfb2b75f43b8bb6a61b8b183359a"
    )


@pytest.fixture
def gpustack_api_key():
    """获取 GPUStack API Key"""
    return os.environ.get(
        "E2E_GPUSTACK_API_KEY",
        "gpustack_14d9f2aee5629a0f_465d73985f7b8f370caecd9e3de838ec",
    )


@pytest.fixture
def gpustack_endpoint():
    """获取 GPUStack Endpoint"""
    return os.environ.get(
        "E2E_GPUSTACK_ENDPOINT", "https://llm-stack.flydiysz.cn"
    )


# =============================================================================
# 通义千问 (Tongyi) 测试
# =============================================================================


@pytest.mark.integration
class TestTongyiConnectivity:
    """通义千问 API 连通性测试"""

    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    @pytest.mark.asyncio
    async def test_list_models(self, tongyi_api_key):
        """测试模型列表接口"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {tongyi_api_key}"},
            )

        assert response.status_code == 200
        data = response.json()
        models = data.get("data", [])
        assert len(models) > 0

    @pytest.mark.asyncio
    async def test_chat_completion(self, tongyi_api_key):
        """测试聊天补全接口（qwen-plus）"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {tongyi_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "qwen-plus",
                    "messages": [{"role": "user", "content": "你好"}],
                    "max_tokens": 10,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0


# =============================================================================
# GPUStack 测试
# =============================================================================


@pytest.mark.integration
class TestGPUStackConnectivity:
    """GPUStack API 连通性测试"""

    @pytest.mark.asyncio
    async def test_list_models(self, gpustack_api_key, gpustack_endpoint):
        """测试模型列表接口"""
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.get(
                f"{gpustack_endpoint}/v1/models",
                headers={"Authorization": f"Bearer {gpustack_api_key}"},
            )

        assert response.status_code == 200
        data = response.json()
        models = data.get("data", [])
        assert len(models) > 0

    @pytest.mark.asyncio
    async def test_chat_completion(self, gpustack_api_key, gpustack_endpoint):
        """测试聊天补全接口（qwen3.5-9b）"""
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.post(
                f"{gpustack_endpoint}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {gpustack_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "qwen3.5-9b",
                    "messages": [{"role": "user", "content": "你好"}],
                    "max_tokens": 10,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "choices" in data

    @pytest.mark.asyncio
    async def test_embedding(self, gpustack_api_key, gpustack_endpoint):
        """测试 Embedding 接口（bge-large-zh-v1.5）"""
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.post(
                f"{gpustack_endpoint}/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {gpustack_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "bge-large-zh-v1.5",
                    "input": "测试文本",
                },
            )

        assert response.status_code == 200
        data = response.json()
        embedding = data["data"][0]["embedding"]
        assert len(embedding) == 1024

    @pytest.mark.asyncio
    async def test_rerank(self, gpustack_api_key, gpustack_endpoint):
        """测试 Rerank 接口（bge-reranker-large）"""
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.post(
                f"{gpustack_endpoint}/v1/rerank",
                headers={
                    "Authorization": f"Bearer {gpustack_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "bge-reranker-large",
                    "query": "什么是机器学习？",
                    "documents": [
                        "机器学习是人工智能的一个分支",
                        "深度学习是机器学习的子领域",
                        "自然语言处理是AI的应用领域",
                    ],
                    "top_n": 3,
                },
            )

        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        assert len(results) == 3
