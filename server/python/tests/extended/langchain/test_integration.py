"""LangChain bridge integration tests"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

from ai_plugin.sdk.entities.model.llm import (
    LLMResult,
    LLMResultChunk,
    LLMResultChunkDelta,
    LLMUsage,
)
from ai_plugin.sdk.entities.model.message import AssistantPromptMessage
from extended.langchain.agents.agent_factory import AgentFactory
from extended.langchain.models.alon_chat import AlonChatModel

pytestmark = pytest.mark.integration


def _make_llm_usage(**overrides) -> LLMUsage:
    defaults = dict(
        prompt_tokens=10,
        prompt_unit_price=Decimal("0.01"),
        prompt_price_unit=Decimal("1"),
        prompt_price=Decimal("0.1"),
        completion_tokens=20,
        completion_unit_price=Decimal("0.02"),
        completion_price_unit=Decimal("1"),
        completion_price=Decimal("0.4"),
        total_tokens=30,
        total_price=Decimal("0.5"),
        currency="USD",
        latency=0.5,
    )
    defaults.update(overrides)
    return LLMUsage(**defaults)


def _make_llm_result(content: str = "Hello!") -> LLMResult:
    return LLMResult(
        model="test-model",
        message=AssistantPromptMessage(content=content),
        usage=_make_llm_usage(),
    )


def _make_llm_chunk(content: str, usage: LLMUsage | None = None) -> LLMResultChunk:
    return LLMResultChunk(
        model="test-model",
        delta=LLMResultChunkDelta(
            index=0,
            message=AssistantPromptMessage(content=content),
            usage=usage,
        ),
    )


class TestMessageAdapterIntegration:
    """Integration: verify message conversion works end-to-end with AlonChatModel."""

    @pytest.mark.asyncio
    async def test_messages_flow_through_alon_chat(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")
        llm_result = _make_llm_result("world")

        with patch("extended.langchain.models.alon_chat.LLMService") as MockLLMService:
            mock_service = AsyncMock()
            mock_service.invoke.return_value = llm_result
            MockLLMService.return_value = mock_service

            messages = [
                SystemMessage(content="You are a helper."),
                HumanMessage(content="Hello"),
            ]
            result = await model.ainvoke(messages)

        assert isinstance(result, AIMessage)
        assert result.content == "world"
        # Verify LLMService received correctly converted messages
        call_kwargs = mock_service.invoke.call_args.kwargs
        platform_msgs = call_kwargs["prompt_messages"]
        assert len(platform_msgs) == 2
        assert platform_msgs[0].role.value == "system"
        assert platform_msgs[1].role.value == "user"


class TestAlonChatModelStreamingIntegration:
    """Integration: verify streaming flow end-to-end."""

    @pytest.mark.asyncio
    async def test_stream_full_flow(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")
        usage = _make_llm_usage(prompt_tokens=5, completion_tokens=10, total_tokens=15)

        async def mock_stream(*args, **kwargs):
            yield _make_llm_chunk("Hello")
            yield _make_llm_chunk(" world")
            yield _make_llm_chunk("!", usage=usage)

        with patch("extended.langchain.models.alon_chat.LLMService") as MockLLMService:
            mock_service = MagicMock()
            mock_service.stream = mock_stream
            MockLLMService.return_value = mock_service

            chunks = []
            async for event in model.astream_events(
                [HumanMessage(content="hi")], version="v2"
            ):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    if chunk is not None:
                        chunks.append(chunk)

        non_empty_chunks = [c for c in chunks if c.content]
        assert len(non_empty_chunks) == 3
        full_content = "".join(c.content for c in non_empty_chunks)
        assert full_content == "Hello world!"


class TestAgentFactoryIntegration:
    """Integration: verify agent creation and model binding."""

    def test_create_executor_with_bound_tools(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")
        factory = AgentFactory(model=model)

        @tool
        def search(query: str) -> str:
            """Search."""
            return f"Result: {query}"

        executor = factory.create_executor(tools=[search])
        assert executor is not None

    def test_create_graph_with_checkpointer(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")
        factory = AgentFactory(model=model)
        checkpointer = MemorySaver()

        @tool
        def search(query: str) -> str:
            """Search."""
            return f"Result: {query}"

        graph = factory.create_graph(tools=[search], checkpointer=checkpointer)
        assert graph is not None


class TestTenantIsolation:
    """Verify tenant isolation through LLMService instantiation."""

    @pytest.mark.asyncio
    async def test_different_tenants_use_different_services(self):
        model_a = AlonChatModel(model="gpt-4", provider="openai", tenant_id="tenant-a")
        model_b = AlonChatModel(model="gpt-4", provider="openai", tenant_id="tenant-b")
        llm_result = _make_llm_result()

        with patch("extended.langchain.models.alon_chat.LLMService") as MockLLMService:
            mock_service = AsyncMock()
            mock_service.invoke.return_value = llm_result
            MockLLMService.return_value = mock_service

            await model_a.ainvoke([HumanMessage(content="hi")])
            await model_b.ainvoke([HumanMessage(content="hi")])

        # LLMService should be called with different tenant_ids
        calls = MockLLMService.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == "tenant-a"
        assert calls[1][0][0] == "tenant-b"
