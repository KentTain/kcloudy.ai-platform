from collections.abc import Generator
from typing import Literal, cast, overload

from ai_plugin.sdk.entities.model.llm import (
    LLMModelConfig,
    LLMResult,
    LLMResultChunk,
    LLMUsage,
    SummaryResult,
)
from ai_plugin.sdk.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageTool,
)
from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class LLMInvocation(BackwardsInvocation[LLMResultChunk]):
    """大语言模型调用类

    用于调用大语言模型进行文本生成，支持流式和非流式输出，支持工具调用。
    """

    @overload
    def invoke(
        self,
        model_config: LLMModelConfig | dict,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: Literal[True] = True,
    ) -> Generator[LLMResultChunk, None, None]: ...

    @overload
    def invoke(
        self,
        model_config: LLMModelConfig | dict,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: Literal[False] = False,
    ) -> LLMResult: ...

    @overload
    def invoke(
        self,
        model_config: LLMModelConfig | dict,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: bool = True,
    ) -> Generator[LLMResultChunk, None, None] | LLMResult: ...

    def invoke(
        self,
        model_config: LLMModelConfig | dict,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: bool = True,
    ) -> Generator[LLMResultChunk, None, None] | LLMResult:
        """调用大语言模型

        Args:
            model_config: 模型配置对象或配置字典
            prompt_messages: 提示消息列表
            tools: 可用工具列表，可选
            stop: 停止词列表，可选
            stream: 是否启用流式输出，默认为True

        Returns:
            根据stream参数返回流式生成器或完整结果对象
        """
        # 如果传入的是字典，转换为模型配置对象
        if isinstance(model_config, dict):
            model_config = LLMModelConfig(**model_config)

        # 构建请求数据
        data = {
            **model_config.model_dump(),
            "prompt_messages": [message.model_dump() for message in prompt_messages],
            "tools": [tool.model_dump() for tool in tools] if tools else None,
            "stop": stop,
            "stream": stream,
        }

        # 流式输出模式
        if stream:
            response = self._backwards_invoke(
                InvokeType.LLM,
                LLMResultChunk,
                data,
            )
            response = cast("Generator[LLMResultChunk, None, None]", response)
            return response

        # 非流式输出模式，需要聚合所有响应块
        result = LLMResult(
            model=model_config.model,
            message=AssistantPromptMessage(content=""),
            usage=LLMUsage.empty_usage(),
        )

        assert isinstance(result.message.content, str)

        # 遍历所有响应块并聚合结果
        for llm_result in self._backwards_invoke(
            InvokeType.LLM,
            LLMResultChunk,
            data,
        ):
            # 聚合文本内容
            if isinstance(llm_result.delta.message.content, str):
                result.message.content += llm_result.delta.message.content

            # 处理工具调用
            if len(llm_result.delta.message.tool_calls) > 0:
                result.message.tool_calls = llm_result.delta.message.tool_calls

            # 聚合使用统计信息
            if llm_result.delta.usage:
                result.usage.prompt_tokens += llm_result.delta.usage.prompt_tokens
                result.usage.completion_tokens += (
                    llm_result.delta.usage.completion_tokens
                )
                result.usage.total_tokens += llm_result.delta.usage.total_tokens

                result.usage.completion_price = llm_result.delta.usage.completion_price
                result.usage.prompt_price = llm_result.delta.usage.prompt_price
                result.usage.total_price = llm_result.delta.usage.total_price
                result.usage.currency = llm_result.delta.usage.currency
                result.usage.latency = llm_result.delta.usage.latency

        return result


class SummaryInvocation(BackwardsInvocation[SummaryResult]):
    """文本摘要调用类

    用于调用系统的文本摘要功能，对长文本进行摘要提取。
    """

    def invoke(
        self,
        text: str,
        instruction: str,
        min_summarize_length: int = 1024,
    ) -> str:
        """调用文本摘要功能

        Args:
            text: 需要摘要的原始文本
            instruction: 摘要指令，指导如何生成摘要
            min_summarize_length: 最小摘要长度阈值，文本长度小于此值时直接返回原文

        Returns:
            生成的摘要文本

        Raises:
            Exception: 当摘要服务没有响应时抛出异常
        """
        # 如果文本长度小于最小摘要长度，直接返回原文
        if len(text) < min_summarize_length:
            return text

        # 构建摘要请求数据
        data = {
            "text": text,
            "instruction": instruction,
        }

        # 调用后端摘要服务
        for llm_result in self._backwards_invoke(
            InvokeType.SYSTEM_SUMMARY,
            SummaryResult,
            data,
        ):
            data = cast("SummaryResult", llm_result)
            return data.summary

        raise Exception("文本摘要服务没有响应")
