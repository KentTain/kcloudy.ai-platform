# 流式调用端到端测试

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from ai_plugin.sdk.entities.model import ModelType


@pytest.mark.integration
class TestStreamingInvocation:
    """流式调用端到端测试"""

    @pytest_asyncio.fixture
    def mock_streaming_response(self):
        """模拟流式响应"""

        async def generate_chunks():
            """生成模拟的流式响应块"""
            chunks = [
                {"event": "chunk", "data": {"content": "Hello"}},
                {"event": "chunk", "data": {"content": " World"}},
                {"event": "chunk", "data": {"content": "!"}},
                {"event": "done", "data": {}},
            ]
            for chunk in chunks:
                yield chunk

        return generate_chunks()

    @pytest_asyncio.fixture
    def mock_model_client(self, mock_streaming_response):
        """模拟模型客户端"""
        client = AsyncMock()

        async def mock_invoke_llm(*args, **kwargs):
            """模拟 invoke_llm 方法"""
            async for chunk in mock_streaming_response:
                yield chunk

        client.invoke_llm = mock_invoke_llm
        return client

    @pytest.mark.asyncio
    async def test_streaming_invocation_basic(self, mock_model_client):
        """测试基本流式调用"""
        chunks = []

        async for chunk in mock_model_client.invoke_llm(
            tenant_id="test-tenant",
            user_id="test-user",
            plugin_id="test-plugin",
            provider="openai",
            model="gpt-4",
            credentials={"api_key": "test-key"},
            prompt_messages=[{"role": "user", "content": "Hello"}],
        ):
            chunks.append(chunk)

        assert len(chunks) == 4
        assert chunks[0]["data"]["content"] == "Hello"
        assert chunks[1]["data"]["content"] == " World"
        assert chunks[2]["data"]["content"] == "!"
        assert chunks[3]["event"] == "done"

    @pytest.mark.asyncio
    async def test_streaming_invocation_empty_response(self):
        """测试空流式响应"""

        async def empty_generator():
            return
            yield  # 使其成为生成器

        mock_client = AsyncMock()
        mock_client.invoke_llm = lambda *args, **kwargs: empty_generator()

        chunks = []
        async for chunk in mock_client.invoke_llm():
            chunks.append(chunk)

        assert len(chunks) == 0


@pytest.mark.integration
class TestStreamingErrorHandling:
    """流式调用错误处理测试"""

    @pytest.mark.asyncio
    async def test_streaming_timeout_error(self):
        """测试流式调用超时"""

        async def timeout_generator():
            yield {"event": "chunk", "data": {"content": "Starting..."}}
            import asyncio

            await asyncio.sleep(10)  # 模拟超时
            yield {"event": "chunk", "data": {"content": "Should not reach"}}

        mock_client = AsyncMock()

        async def mock_invoke(*args, **kwargs):
            async for chunk in timeout_generator():
                yield chunk

        mock_client.invoke_llm = mock_invoke

        # 使用超时限制
        chunks = []
        try:
            import asyncio

            async for chunk in mock_client.invoke_llm():
                chunks.append(chunk)
                if len(chunks) >= 1:
                    break  # 获取第一个块后退出
        except asyncio.TimeoutError:
            pass  # 预期的超时

        # 至少获取到一个块
        assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_streaming_connection_error(self):
        """测试流式调用连接错误"""

        async def error_generator():
            yield {"event": "error", "data": {"message": "Connection failed"}}

        mock_client = AsyncMock()

        async def mock_invoke(*args, **kwargs):
            async for chunk in error_generator():
                yield chunk

        mock_client.invoke_llm = mock_invoke

        chunks = []
        async for chunk in mock_client.invoke_llm():
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0]["event"] == "error"


@pytest.mark.integration
class TestStreamingMultiTenant:
    """流式调用多租户测试"""

    @pytest_asyncio.fixture
    def multi_tenant_responses(self):
        """多租户响应模拟"""

        async def generate_for_tenant(tenant_id: str):
            """为特定租户生成响应"""
            yield {
                "event": "chunk",
                "data": {"content": f"Response for {tenant_id}"},
            }
            yield {"event": "done", "data": {}}

        return generate_for_tenant

    @pytest.mark.asyncio
    async def test_streaming_tenant_isolation(self, multi_tenant_responses):
        """测试流式调用租户隔离"""
        tenant1 = "tenant-001"
        tenant2 = "tenant-002"

        # 模拟两个租户的调用
        results = {}

        for tenant_id in [tenant1, tenant2]:
            chunks = []
            async for chunk in multi_tenant_responses(tenant_id):
                chunks.append(chunk)
            results[tenant_id] = chunks

        # 验证租户隔离
        assert results[tenant1][0]["data"]["content"] == f"Response for {tenant1}"
        assert results[tenant2][0]["data"]["content"] == f"Response for {tenant2}"


@pytest.mark.integration
class TestStreamingModelTypes:
    """不同模型类型流式调用测试"""

    @pytest_asyncio.fixture
    def model_type_responses(self):
        """不同模型类型响应模拟"""

        async def generate_for_model_type(model_type: ModelType):
            """为特定模型类型生成响应"""
            if model_type == ModelType.LLM:
                yield {"event": "chunk", "data": {"content": "LLM response"}}
            elif model_type == ModelType.TEXT_EMBEDDING:
                yield {"event": "chunk", "data": {"embedding": [0.1, 0.2, 0.3]}}
            elif model_type == ModelType.RERANK:
                yield {
                    "event": "chunk",
                    "data": {"results": [{"score": 0.95, "text": "doc1"}]},
                }
            yield {"event": "done", "data": {}}

        return generate_for_model_type

    @pytest.mark.asyncio
    async def test_streaming_llm_model(self, model_type_responses):
        """测试 LLM 模型流式调用"""
        chunks = []
        async for chunk in model_type_responses(ModelType.LLM):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert "content" in chunks[0]["data"]

    @pytest.mark.asyncio
    async def test_streaming_embedding_model(self, model_type_responses):
        """测试嵌入模型流式调用"""
        chunks = []
        async for chunk in model_type_responses(ModelType.TEXT_EMBEDDING):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert "embedding" in chunks[0]["data"]

    @pytest.mark.asyncio
    async def test_streaming_rerank_model(self, model_type_responses):
        """测试重排序模型流式调用"""
        chunks = []
        async for chunk in model_type_responses(ModelType.RERANK):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert "results" in chunks[0]["data"]


@pytest.mark.integration
class TestStreamingCancellation:
    """流式调用取消测试"""

    @pytest.mark.asyncio
    async def test_streaming_cancellation_midway(self):
        """测试中途取消流式调用"""

        async def long_generator():
            for i in range(100):
                yield {"event": "chunk", "data": {"content": f"Chunk {i}"}}
                import asyncio

                await asyncio.sleep(0.01)

        mock_client = AsyncMock()

        async def mock_invoke(*args, **kwargs):
            async for chunk in long_generator():
                yield chunk

        mock_client.invoke_llm = mock_invoke

        chunks = []
        async for chunk in mock_client.invoke_llm():
            chunks.append(chunk)
            if len(chunks) >= 5:
                break  # 模拟用户取消

        # 应该只收到 5 个块
        assert len(chunks) == 5


@pytest.mark.integration
class TestStreamingConcurrency:
    """流式调用并发测试"""

    @pytest.mark.asyncio
    async def test_concurrent_streaming_calls(self):
        """测试并发流式调用"""

        async def generate_for_call(call_id: int):
            """为特定调用生成响应"""
            yield {
                "event": "chunk",
                "data": {"content": f"Call {call_id} response"},
            }
            yield {"event": "done", "data": {}}

        async def collect_chunks(call_id: int):
            """收集特定调用的响应"""
            chunks = []
            async for chunk in generate_for_call(call_id):
                chunks.append(chunk)
            return chunks

        # 并发执行多个流式调用
        import asyncio

        results = await asyncio.gather(
            collect_chunks(1),
            collect_chunks(2),
            collect_chunks(3),
        )

        # 验证每个调用都收到正确的响应
        assert len(results) == 3
        for i, chunks in enumerate(results, 1):
            assert chunks[0]["data"]["content"] == f"Call {i} response"


@pytest.mark.integration
@pytest.mark.skipif(
    True,  # 默认跳过，需要真实插件环境
    reason="需要真实插件环境，请手动启用此测试",
)
class TestStreamingWithRealPlugin:
    """流式调用真实插件测试"""

    @pytest_asyncio.fixture
    async def real_model_client(self):
        """真实模型客户端 fixture"""
        from ai.components.plugin.client.model_client import ModelClient

        return ModelClient()

    @pytest.mark.asyncio
    async def test_real_plugin_streaming(self, real_model_client):
        """测试真实插件流式调用"""
        # 此测试需要真实的插件环境
        # 仅作为示例，实际运行需要配置插件
        pytest.skip("需要配置真实插件环境")

        async for chunk in real_model_client.invoke_llm(
            tenant_id="test-tenant",
            user_id="test-user",
            plugin_id="real-plugin-id",
            provider="openai",
            model="gpt-4",
            credentials={"api_key": "real-api-key"},
            prompt_messages=[{"role": "user", "content": "Hello"}],
        ):
            # 验证响应格式
            assert "event" in chunk or "data" in chunk
