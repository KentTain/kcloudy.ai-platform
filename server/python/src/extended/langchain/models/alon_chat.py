"""
AlonChatModel - LangChain BaseChatModel bridge to platform LLMService

Provides async non-streaming (_agenerate) and streaming (_astream)
methods that delegate to the platform LLMService.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Sequence
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.messages.content import ToolCall
from langchain_core.outputs import (
    ChatGeneration,
    ChatGenerationChunk,
    ChatResult,
)
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from ai.components.model.services.llm_service import LLMService
from ai_plugin.sdk.entities.model.message import PromptMessageTool
from extended.langchain.models.message_adapter import (
    MessageAdapter,
    _platform_content_to_lc,
)


def _convert_tool(tool: BaseTool | dict | Callable) -> PromptMessageTool:
    """Convert a LangChain tool to platform PromptMessageTool format."""
    if isinstance(tool, PromptMessageTool):
        return tool
    if isinstance(tool, dict):
        return PromptMessageTool(**tool)
    if isinstance(tool, BaseTool):
        return PromptMessageTool(
            name=tool.name,
            description=tool.description or "",
            parameters=tool.args_schema.model_json_schema()
            if tool.args_schema
            else {"type": "object", "properties": {}},
        )
    if callable(tool):
        from langchain_core.tools import tool as tool_decorator

        converted = tool_decorator(tool)
        return _convert_tool(converted)
    raise ValueError(f"Cannot convert tool of type {type(tool)}")


class AlonChatModel(BaseChatModel):
    """LangChain ChatModel that bridges to platform LLMService."""

    model: str
    provider: str
    tenant_id: str
    user_id: str | None = None
    model_parameters: dict = {}

    @property
    def _llm_type(self) -> str:
        return "alon-chat-model"

    @property
    def _identifying_params(self) -> dict:
        return {
            "model": self.model,
            "provider": self.provider,
            "tenant_id": self.tenant_id,
        }

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable | BaseTool],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> Runnable:
        """Bind tools to the model for tool calling."""
        platform_tools = [_convert_tool(t) for t in tools]
        return self.bind(tools=platform_tools, **kwargs)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        raise NotImplementedError("Use async method ainvoke instead")

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        llm_service = LLMService(self.tenant_id)
        prompt_messages = MessageAdapter.to_platform_messages(messages)
        tools = kwargs.get("tools")

        result = await llm_service.invoke(
            prompt_messages=prompt_messages,
            model=self.model,
            provider=self.provider,
            model_parameters=self.model_parameters or None,
            tools=tools,
            stop=stop,
            user=self.user_id,
        )

        content = _platform_content_to_lc(result.message.content) or ""
        usage = result.usage
        ai_message = AIMessage(content=content)
        if result.message.tool_calls:
            import json

            ai_message = AIMessage(
                content="",
                content_blocks=[
                    ToolCall(
                        type="tool_call",
                        id=tc.id,
                        name=tc.function.name,
                        args=json.loads(tc.function.arguments)
                        if tc.function.arguments
                        else {},
                    )
                    for tc in result.message.tool_calls
                ],
            )

        return ChatResult(
            generations=[
                ChatGeneration(
                    message=ai_message,
                    generation_info={
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                    },
                )
            ],
            llm_output={"model": self.model},
        )

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        llm_service = LLMService(self.tenant_id)
        prompt_messages = MessageAdapter.to_platform_messages(messages)
        tools = kwargs.get("tools")

        async for chunk in llm_service.stream(
            prompt_messages=prompt_messages,
            model=self.model,
            provider=self.provider,
            model_parameters=self.model_parameters or None,
            tools=tools,
            stop=stop,
            user=self.user_id,
        ):
            content = _platform_content_to_lc(chunk.delta.message.content) or ""
            if not content:
                continue
            usage_info = {}
            if chunk.delta.usage:
                usage_info = {
                    "prompt_tokens": chunk.delta.usage.prompt_tokens,
                    "completion_tokens": chunk.delta.usage.completion_tokens,
                    "total_tokens": chunk.delta.usage.total_tokens,
                }
            yield ChatGenerationChunk(
                message=AIMessageChunk(content=content),
                generation_info=usage_info or None,
            )
