# Provider API 连通性集成测试

# API Key fixtures 来自上层 ai/conftest.py

import httpx
import pytest

# =============================================================================
# 通义千问 (Tongyi) 测试
# =============================================================================


@pytest.mark.integration
class TestTongyiConnectivity:
    """通义千问 API 连通性测试"""

    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    @pytest.mark.asyncio
    async def test_list_models(
        self,
        tongyi_api_key_available: bool,
        tongyi_api_key: str,
    ):
        """测试模型列表接口"""
        if not tongyi_api_key_available:
            pytest.skip("Tongyi API Key 不可用")

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
    async def test_chat_completion(
        self,
        tongyi_api_key_available: bool,
        tongyi_api_key: str,
    ):
        """测试聊天补全接口（qwen-plus）"""
        if not tongyi_api_key_available:
            pytest.skip("Tongyi API Key 不可用")

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
    async def test_list_models(
        self,
        gpustack_api_key_available: bool,
        gpustack_api_key: str,
        gpustack_endpoint: str,
    ):
        """测试模型列表接口"""
        if not gpustack_api_key_available:
            pytest.skip("GPUStack API Key 不可用")

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
    async def test_chat_completion(
        self,
        gpustack_api_key_available: bool,
        gpustack_api_key: str,
        gpustack_endpoint: str,
    ):
        """测试聊天补全接口（qwen3.5-9b）"""
        if not gpustack_api_key_available:
            pytest.skip("GPUStack API Key 不可用")

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
    async def test_embedding(
        self,
        gpustack_api_key_available: bool,
        gpustack_api_key: str,
        gpustack_endpoint: str,
    ):
        """测试 Embedding 接口（bge-large-zh-v1.5）"""
        if not gpustack_api_key_available:
            pytest.skip("GPUStack API Key 不可用")

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
    async def test_rerank(
        self,
        gpustack_api_key_available: bool,
        gpustack_api_key: str,
        gpustack_endpoint: str,
    ):
        """测试 Rerank 接口（bge-reranker-large）"""
        if not gpustack_api_key_available:
            pytest.skip("GPUStack API Key 不可用")

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


# =============================================================================
# 硅基流动 (SiliconFlow) 测试
# =============================================================================


@pytest.mark.integration
class TestSiliconFlowConnectivity:
    """硅基流动 API 连通性测试"""

    BASE_URL = "https://api.siliconflow.cn/v1"

    @pytest.mark.asyncio
    async def test_list_models(
        self,
        siliconflow_api_key_available: bool,
        siliconflow_api_key: str,
    ):
        """测试模型列表接口"""
        if not siliconflow_api_key_available:
            pytest.skip("SiliconFlow API Key 不可用")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {siliconflow_api_key}"},
            )

        assert response.status_code == 200
        data = response.json()
        models = data.get("data", [])
        assert len(models) > 0

    @pytest.mark.asyncio
    async def test_chat_completion(
        self,
        siliconflow_api_key_available: bool,
        siliconflow_api_key: str,
    ):
        """测试聊天补全接口（Qwen/Qwen2.5-7B-Instruct）"""
        if not siliconflow_api_key_available:
            pytest.skip("SiliconFlow API Key 不可用")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {siliconflow_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "Qwen/Qwen2.5-7B-Instruct",
                    "messages": [{"role": "user", "content": "你好"}],
                    "max_tokens": 10,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0

    @pytest.mark.asyncio
    async def test_embedding(
        self,
        siliconflow_api_key_available: bool,
        siliconflow_api_key: str,
    ):
        """测试 Embedding 接口（BAAI/bge-large-zh-v1.5）"""
        if not siliconflow_api_key_available:
            pytest.skip("SiliconFlow API Key 不可用")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/embeddings",
                headers={
                    "Authorization": f"Bearer {siliconflow_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "BAAI/bge-large-zh-v1.5",
                    "input": "测试文本",
                    "encoding_format": "float",
                },
            )

        assert response.status_code == 200
        data = response.json()
        embedding = data["data"][0]["embedding"]
        assert len(embedding) == 1024


# =============================================================================
# 深度求索 (DeepSeek) 测试
# =============================================================================


@pytest.mark.integration
class TestDeepSeekConnectivity:
    """深度求索 API 连通性测试"""

    BASE_URL = "https://api.deepseek.com/v1"

    @pytest.mark.asyncio
    async def test_list_models(
        self,
        deepseek_api_key_available: bool,
        deepseek_api_key: str,
    ):
        """测试模型列表接口"""
        if not deepseek_api_key_available:
            pytest.skip("DeepSeek API Key 不可用")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {deepseek_api_key}"},
            )

        assert response.status_code == 200
        data = response.json()
        models = data.get("data", [])
        assert len(models) > 0

    @pytest.mark.asyncio
    async def test_chat_completion(
        self,
        deepseek_api_key_available: bool,
        deepseek_api_key: str,
    ):
        """测试聊天补全接口（deepseek-chat）"""
        if not deepseek_api_key_available:
            pytest.skip("DeepSeek API Key 不可用")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "你好"}],
                    "max_tokens": 10,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
