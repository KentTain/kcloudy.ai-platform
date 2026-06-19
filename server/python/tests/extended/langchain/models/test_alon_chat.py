"""AlonChatModel unit tests"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from ai_plugin.sdk.entities.model.llm import (
    LLMResult,
    LLMResultChunk,
    LLMResultChunkDelta,
    LLMUsage,
)
from ai_plugin.sdk.entities.model.message import AssistantPromptMessage
from extended.langchain.models.alon_chat import AlonChatModel


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


def _make_llm_result(content: str = "hello") -> LLMResult:
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


class TestAlonChatModelInit:
    def test_llm_type(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")
        assert model._llm_type == "alon-chat-model"

    def test_identifying_params(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")
        params = model._identifying_params
        assert params["model"] == "gpt-4"
        assert params["provider"] == "openai"
        assert params["tenant_id"] == "t1"

    def test_default_model_parameters(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")
        assert model.model_parameters == {}


class TestAlonChatModelGenerate:
    def test_sync_generate_raises(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")
        with pytest.raises(NotImplementedError):
            model._generate([HumanMessage(content="hi")])


class TestAlonChatModelAgenerate:
    @pytest.mark.asyncio
    async def test_agenerate_success(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")
        llm_result = _make_llm_result("world")

        with patch("extended.langchain.models.alon_chat.LLMService") as MockLLMService:
            mock_service = AsyncMock()
            mock_service.invoke.return_value = llm_result
            MockLLMService.return_value = mock_service

            result = await model._agenerate([HumanMessage(content="hi")])

        assert isinstance(result, ChatResult)
        assert len(result.generations) == 1
        gen = result.generations[0]
        assert isinstance(gen, ChatGeneration)
        assert isinstance(gen.message, AIMessage)
        assert gen.message.content == "world"
        assert gen.generation_info["prompt_tokens"] == 10
        assert gen.generation_info["completion_tokens"] == 20
        assert gen.generation_info["total_tokens"] == 30

    @pytest.mark.asyncio
    async def test_agenerate_with_model_parameters(self):
        model = AlonChatModel(
            model="gpt-4",
            provider="openai",
            tenant_id="t1",
            model_parameters={"temperature": 0.7},
        )
        llm_result = _make_llm_result()

        with patch("extended.langchain.models.alon_chat.LLMService") as MockLLMService:
            mock_service = AsyncMock()
            mock_service.invoke.return_value = llm_result
            MockLLMService.return_value = mock_service

            await model._agenerate([HumanMessage(content="hi")])

            call_kwargs = mock_service.invoke.call_args
            assert call_kwargs.kwargs["model_parameters"]["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_agenerate_with_stop(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")
        llm_result = _make_llm_result()

        with patch("extended.langchain.models.alon_chat.LLMService") as MockLLMService:
            mock_service = AsyncMock()
            mock_service.invoke.return_value = llm_result
            MockLLMService.return_value = mock_service

            await model._agenerate([HumanMessage(content="hi")], stop=["\n"])

            call_kwargs = mock_service.invoke.call_args
            assert call_kwargs.kwargs["stop"] == ["\n"]

    @pytest.mark.asyncio
    async def test_agenerate_propagates_error(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")

        with patch("extended.langchain.models.alon_chat.LLMService") as MockLLMService:
            mock_service = AsyncMock()
            mock_service.invoke.side_effect = ValueError("no provider")
            MockLLMService.return_value = mock_service

            with pytest.raises(ValueError, match="no provider"):
                await model._agenerate([HumanMessage(content="hi")])


class TestAlonChatModelAstream:
    @pytest.mark.asyncio
    async def test_astream_yields_chunks(self):
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
            async for chunk in model._astream([HumanMessage(content="hi")]):
                chunks.append(chunk)

        assert len(chunks) == 3
        assert isinstance(chunks[0], ChatGenerationChunk)
        assert isinstance(chunks[0].message, AIMessageChunk)
        assert chunks[0].message.content == "Hello"
        assert chunks[1].message.content == " world"
        # Last chunk should have usage info
        assert chunks[2].generation_info["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_astream_empty_content_skipped(self):
        model = AlonChatModel(model="gpt-4", provider="openai", tenant_id="t1")

        async def mock_stream(*args, **kwargs):
            yield _make_llm_chunk("")
            yield _make_llm_chunk("data")

        with patch("extended.langchain.models.alon_chat.LLMService") as MockLLMService:
            mock_service = MagicMock()
            mock_service.stream = mock_stream
            MockLLMService.return_value = mock_service

            chunks = []
            async for chunk in model._astream([HumanMessage(content="hi")]):
                chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].message.content == "data"
