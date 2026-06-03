"""
大语言模型基类

迁移自 Alon: src/alon/components/model/model_providers/__base__/large_language_model.py

提供大语言模型的基础实现，通过插件系统调用实际的 LLM 服务
"""

import time
import uuid
from collections.abc import AsyncGenerator, Sequence

from loguru import logger
from pydantic import ConfigDict

from ai.components.model.internal.configs import model_config
from ai.components.model.model_providers.__base__.ai_model import AIModelImpl
from ai.components.plugin.client.model_client import ModelClient
from ai_plugin.sdk.entities.model import ModelType, PriceType
from ai_plugin.sdk.entities.model.llm import LLMResult, LLMResultChunk, LLMUsage
from ai_plugin.sdk.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageContent,
    PromptMessageContentUnionTypes,
    PromptMessageTool,
    TextPromptMessageContent,
)

_logger = logger.bind(name=__name__)


def _gen_tool_call_id() -> str:
    """生成工具调用 ID"""
    return f"chatcmpl-tool-{str(uuid.uuid4().hex)}"


def _increase_tool_call(
    new_tool_calls: list[AssistantPromptMessage.ToolCall],
    existing_tools_calls: list[AssistantPromptMessage.ToolCall],
):
    """
    将增量的工具调用更新合并到现有的工具调用中

    :param new_tool_calls: 要合并的新工具调用增量列表
    :param existing_tools_calls: 要修改的现有工具调用列表（原地修改）
    """

    def get_tool_call(tool_call_id: str):
        """
        根据 ID 获取或创建工具调用

        :param tool_call_id: 工具调用 ID
        :return: 现有或新的工具调用
        """
        if not tool_call_id:
            return existing_tools_calls[-1]

        _tool_call = next(
            (
                _tool_call
                for _tool_call in existing_tools_calls
                if _tool_call.id == tool_call_id
            ),
            None,
        )
        if _tool_call is None:
            _tool_call = AssistantPromptMessage.ToolCall(
                id=tool_call_id,
                type="function",
                function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                    name="", arguments=""
                ),
            )
            existing_tools_calls.append(_tool_call)

        return _tool_call

    for new_tool_call in new_tool_calls:
        # 为有函数名但没有 ID 的工具调用生成 ID 以便跟踪
        if new_tool_call.function.name and not new_tool_call.id:
            new_tool_call.id = _gen_tool_call_id()
        # 获取工具调用
        tool_call = get_tool_call(new_tool_call.id)
        # 更新工具调用
        if new_tool_call.id:
            tool_call.id = new_tool_call.id
        if new_tool_call.type:
            tool_call.type = new_tool_call.type
        if new_tool_call.function.name:
            tool_call.function.name = new_tool_call.function.name
        if new_tool_call.function.arguments:
            tool_call.function.arguments += new_tool_call.function.arguments


class LargeLanguageModelImpl(AIModelImpl):
    """
    大语言模型基础类

    提供大语言模型的调用、token 计数等核心功能
    """

    model_type: ModelType = ModelType.LLM

    # pydantic 配置
    model_config = ConfigDict(protected_namespaces=())

    async def invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict | None = None,
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ) -> LLMResult | AsyncGenerator[LLMResultChunk, None]:
        """
        调用大语言模型

        :param model: 模型名称
        :param credentials: 模型凭证
        :param prompt_messages: 提示消息
        :param model_parameters: 模型参数
        :param tools: 工具调用
        :param stop: 停止词
        :param stream: 是否流式响应
        :param user: 唯一用户 ID
        :return: 完整响应或流式响应 chunk 异步生成器结果
        """
        # 验证和过滤模型参数
        if model_parameters is None:
            model_parameters = {}

        # 记录调用开始时间
        self.started_at = time.perf_counter()

        result: LLMResult | AsyncGenerator[LLMResultChunk, None]

        try:
            # 通过插件模型管理器调用 LLM
            model_client = ModelClient()

            result = model_client.invoke_llm(
                tenant_id=self.tenant_id,
                user_id=user or "unknown",
                plugin_id=self.plugin_id,
                provider=self.provider_name,
                model=model,
                credentials=credentials,
                model_parameters=model_parameters,
                prompt_messages=prompt_messages,
                tools=tools,
                stop=list(stop) if stop else None,
            )

            # 如果不是流式响应，需要汇总结果
            if not stream:
                content = ""
                content_list = []
                usage = LLMUsage.empty_usage()
                system_fingerprint = None
                tools_calls: list[AssistantPromptMessage.ToolCall] = []

                # 遍历结果流并汇总
                async for chunk in result:
                    if isinstance(chunk.delta.message.content, str):
                        content += chunk.delta.message.content
                    elif isinstance(chunk.delta.message.content, list):
                        content_list.extend(chunk.delta.message.content)
                    if chunk.delta.message.tool_calls:
                        _increase_tool_call(chunk.delta.message.tool_calls, tools_calls)

                    usage = chunk.delta.usage or LLMUsage.empty_usage()
                    system_fingerprint = chunk.system_fingerprint

                # 构建最终结果
                result = LLMResult(
                    model=model,
                    prompt_messages=prompt_messages,
                    message=AssistantPromptMessage(
                        content=content or content_list,
                        tool_calls=tools_calls,
                    ),
                    usage=usage,
                    system_fingerprint=system_fingerprint,
                )
        except Exception as e:
            # 转换并抛出统一错误
            raise self._transform_invoke_error(e)

        # 处理流式响应结果
        if stream and isinstance(result, AsyncGenerator):
            return self._invoke_result_generator(
                model=model,
                result=result,
                credentials=credentials,
                prompt_messages=prompt_messages,
                model_parameters=model_parameters,
                tools=tools,
                stop=stop,
                stream=stream,
                user=user,
            )
        elif isinstance(result, LLMResult):
            return result

        return result

    async def _invoke_result_generator(
        self,
        model: str,
        result: AsyncGenerator[LLMResultChunk, None],
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ) -> AsyncGenerator[LLMResultChunk, None]:
        """
        调用结果生成器，处理流式响应

        :param model: 模型名称
        :param result: 结果异步生成器
        :param credentials: 模型凭证
        :param prompt_messages: 提示消息
        :param model_parameters: 模型参数
        :param tools: 工具列表
        :param stop: 停止词
        :param stream: 是否流式响应
        :param user: 用户 ID
        :return: 结果异步生成器
        """
        message_content: list[PromptMessageContentUnionTypes] = []
        usage = None
        system_fingerprint = None
        real_model = model

        def _update_message_content(
            content: str | list[PromptMessageContentUnionTypes] | None,
        ):
            """更新消息内容"""
            if not content:
                return
            if isinstance(content, list):
                message_content.extend(content)
                return
            if isinstance(content, str):
                message_content.append(TextPromptMessageContent(data=content))
                return

        try:
            # 遍历结果流
            async for chunk in result:
                # 根据 https://github.com/langgenius/dify/issues/17799，
                # 我们在插件守护进程端移除了 chunk 中的 prompt_messages。
                # 为了确保兼容性，我们在这里重新添加 prompt_messages。
                chunk.prompt_messages = prompt_messages
                yield chunk

                # 更新消息内容
                _update_message_content(chunk.delta.message.content)

                # 更新实际模型名称和使用情况
                real_model = chunk.model
                if chunk.delta.usage:
                    usage = chunk.delta.usage

                if chunk.system_fingerprint:
                    system_fingerprint = chunk.system_fingerprint
        except Exception as e:
            raise self._transform_invoke_error(e)

    async def get_num_tokens(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
    ) -> int:
        """
        获取给定提示消息的 token 数量

        :param model: 模型名称
        :param credentials: 模型凭证
        :param prompt_messages: 提示消息
        :param tools: 工具调用
        :return: token 数量
        """
        # 如果启用了基于插件的 token 计数
        if model_config.PLUGIN_BASED_TOKEN_COUNTING_ENABLED:
            _logger.info("基于插件的 token 计数已启用，使用插件 token 计数")
            model_client = ModelClient()

            return await model_client.get_llm_num_tokens(
                tenant_id=self.tenant_id,
                user_id="unknown",
                plugin_id=self.plugin_id,
                provider=self.provider_name,
                model=model,
                credentials=credentials,
                prompt_messages=prompt_messages,
                tools=tools,
            )

        else:
            _logger.info("基于插件的 token 计数未启用，使用本地 token 计数")
            all_text = ""
            for message in prompt_messages:
                role = message.role
                all_text += role.value + ":\n"

                msg: str | list[PromptMessageContent] | None = (
                    PromptMessage.transform_content(message.content)
                )
                if isinstance(msg, str):
                    all_text += msg
                elif isinstance(msg, list):
                    for item in msg:
                        if isinstance(item, str):
                            all_text += item
                        else:
                            if hasattr(item, "data"):
                                all_text += str(item.data)
                            else:
                                raise ValueError(
                                    f"Unexpected content type: {type(item)}"
                                )

            if tools:
                all_text += "\n\ntools:\n```json\n"
                for tool in tools:
                    all_text += tool.model_dump_json()
                all_text += "\n```\n"

            _logger.debug(f"Token counting text length: {len(all_text)}")

            # 使用 GPT-2 tokenizer 进行本地 token 计数
            from ai.components.model.model_providers.__base__.tokenizers.gpt2_tokenizer import (
                GPT2Tokenizer,
            )

            num = GPT2Tokenizer.get_num_tokens(all_text)
            return num

    async def _calc_response_usage(
        self,
        model: str,
        credentials: dict,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> LLMUsage:
        """
        计算响应使用情况

        :param model: 模型名称
        :param credentials: 模型凭证
        :param prompt_tokens: 输入 token 数量
        :param completion_tokens: 完成 token 数量
        :return: 使用情况统计
        """
        # 获取输入价格信息
        prompt_price_info = await self.get_price(
            model=model,
            credentials=credentials,
            price_type=PriceType.INPUT,
            tokens=prompt_tokens,
        )

        # 获取输出价格信息
        completion_price_info = await self.get_price(
            model=model,
            credentials=credentials,
            price_type=PriceType.OUTPUT,
            tokens=completion_tokens,
        )

        # 构建使用情况统计
        usage = LLMUsage(
            prompt_tokens=prompt_tokens,
            prompt_unit_price=prompt_price_info.unit_price,
            prompt_price_unit=prompt_price_info.unit,
            prompt_price=prompt_price_info.total_amount,
            completion_tokens=completion_tokens,
            completion_unit_price=completion_price_info.unit_price,
            completion_price_unit=completion_price_info.unit,
            completion_price=completion_price_info.total_amount,
            total_tokens=prompt_tokens + completion_tokens,
            total_price=prompt_price_info.total_amount
            + completion_price_info.total_amount,
            currency=prompt_price_info.currency,
            latency=time.perf_counter() - self.started_at,
        )

        return usage
