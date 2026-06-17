"""基于聊天的语言模型实现模块。

本模块实现了基于 OpenAI Chat Completions API 的语言模型,支持:
- 标准的对话补全
- JSON 格式输出(原生和手动解析两种模式)
- 自动重试和 JSON 修复
- 历史消息管理
"""

import logging
from typing import Unpack

from ai.components.graphrag.llm.base import BaseLLM
from ai.components.graphrag.llm.openai._prompts import JSON_CHECK_PROMPT
from ai.components.graphrag.llm.openai.openai_configuration import OpenAIConfiguration
from ai.components.graphrag.llm.openai.types import OpenAIClientTypes
from ai.components.graphrag.llm.openai.utils import (
    get_completion_llm_args,
    try_parse_json_object,
)
from ai.components.graphrag.llm.types import (
    CompletionInput,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)

log = logging.getLogger(__name__)

# JSON 生成最大重试次数
_MAX_GENERATION_RETRIES = 3
# JSON 生成失败错误消息
FAILED_TO_CREATE_JSON_ERROR = "Failed to generate valid JSON output"


class OpenAIChatLLM(BaseLLM[CompletionInput, CompletionOutput]):
    """
    基于聊天的 LLM 实现。

    使用 OpenAI 的 Chat Completions API 实现的语言模型,支持多轮对话,
    JSON 输出和自动重试等功能。
    """

    _client: OpenAIClientTypes
    _configuration: OpenAIConfiguration

    def __init__(self, client: OpenAIClientTypes, configuration: OpenAIConfiguration):
        """
        初始化实例。

        Args:
            client (OpenAIClientTypes): client 参数。
            configuration (OpenAIConfiguration): configuration 参数。
        """
        self.client = client
        self.configuration = configuration

    async def _execute_llm(
        self, input: CompletionInput, **kwargs: Unpack[LLMInput]
    ) -> CompletionOutput | None:
        """
        执行execute_llm。

        Args:
            input (CompletionInput): input 参数。
            kwargs (Unpack[LLMInput]): kwargs 参数。

        Returns:
            处理结果。
        """
        args = get_completion_llm_args(
            kwargs.get("model_parameters"), self.configuration
        )
        history = kwargs.get("history") or []
        # 构建消息列表:历史消息 + 当前用户输入
        messages = [
            *history,
            {"role": "user", "content": input},
        ]
        completion = await self.client.chat.completions.create(
            messages=messages, **args
        )
        return completion.choices[0].message.content

    async def _invoke_json(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[CompletionOutput]:
        """
        调用invoke_json。

        Args:
            input (CompletionInput): input 参数。
            kwargs (Unpack[LLMInput]): kwargs 参数。

        Returns:
            处理结果。
        """
        name = kwargs.get("name") or "unknown"
        is_response_valid = kwargs.get("is_response_valid") or (lambda _x: True)

        async def generate(
            attempt: int | None = None,
        ) -> LLMOutput[CompletionOutput]:
            """生成 JSON 输出的内部函数."""
            call_name = name if attempt is None else f"{name}@{attempt}"
            # 根据模型能力选择 JSON 生成方式
            return (
                await self._native_json(input, **{**kwargs, "name": call_name})
                if self.configuration.model_supports_json
                else await self._manual_json(input, **{**kwargs, "name": call_name})
            )

        def is_valid(x: dict | None) -> bool:
            """检查 JSON 是否有效."""
            return x is not None and is_response_valid(x)

        # 首次生成
        result = await generate()
        retry = 0
        # 如果结果无效,进行重试
        while not is_valid(result.json) and retry < _MAX_GENERATION_RETRIES:
            result = await generate(retry)
            retry += 1

        if is_valid(result.json):
            return result

        # 达到最大重试次数仍失败
        error_msg = f"{FAILED_TO_CREATE_JSON_ERROR} - Faulty JSON: {result.json!s}"
        raise RuntimeError(error_msg)

    async def _native_json(
        self, input: CompletionInput, **kwargs: Unpack[LLMInput]
    ) -> LLMOutput[CompletionOutput]:
        """
        处理native_json。

        Args:
            input (CompletionInput): input 参数。
            kwargs (Unpack[LLMInput]): kwargs 参数。

        Returns:
            处理结果。
        """
        result = await self._invoke(
            input,
            **{
                **kwargs,
                "model_parameters": {
                    **(kwargs.get("model_parameters") or {}),
                    "response_format": {"type": "json_object"},
                },
            },
        )

        output, json_output = try_parse_json_object(result.output or "")

        return LLMOutput[CompletionOutput](
            output=output,
            json=json_output,
            history=result.history,
        )

    async def _manual_json(
        self, input: CompletionInput, **kwargs: Unpack[LLMInput]
    ) -> LLMOutput[CompletionOutput]:
        """
        处理manual_json。

        Args:
            input (CompletionInput): input 参数。
            kwargs (Unpack[LLMInput]): kwargs 参数。

        Returns:
            处理结果。
        """
        # 获取 LLM 输出并尝试解析为 JSON
        result = await self._invoke(input, **kwargs)
        history = result.history or []
        output, json_output = try_parse_json_object(result.output or "")
        if json_output:
            return LLMOutput[CompletionOutput](
                output=result.output, json=json_output, history=history
            )

        # 如果没有返回正确格式的 JSON,重试
        log.warning("error parsing llm json, retrying")

        # 如果清理后的 JSON 仍无法解析,使用 LLM 重新格式化(可能抛出异常)
        result = await self._try_clean_json_with_llm(output, **kwargs)
        output, json_output = try_parse_json_object(result.output or "")

        return LLMOutput[CompletionOutput](
            output=output,
            json=json_output,
            history=history,
        )

    async def _try_clean_json_with_llm(
        self, output: str, **kwargs: Unpack[LLMInput]
    ) -> LLMOutput[CompletionOutput]:
        """
        处理try_clean_json_llm。

        Args:
            output (str): output 参数。
            kwargs (Unpack[LLMInput]): kwargs 参数。

        Returns:
            处理结果。
        """
        name = kwargs.get("name") or "unknown"
        return await self._invoke(
            JSON_CHECK_PROMPT,
            **{
                **kwargs,
                "variables": {"input_text": output},
                "name": f"fix_json@{name}",
            },
        )
