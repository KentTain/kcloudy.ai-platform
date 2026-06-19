import json
import sys
from collections.abc import Sequence
from typing import cast

from loguru import logger

from ai.components.model.callbacks.base_callback import Callback
from ai.components.model.model_providers.__base__.ai_model import AIModelImpl

from ai_plugin.sdk.entities.model.message import PromptMessage, PromptMessageTool

from ai_plugin.sdk.entities.model.llm import LLMResult, LLMResultChunk


_logger = logger.bind(name=__name__)


class LoggingCallback(Callback):
    """
    日志回调类

    用于记录大语言模型调用过程中的详细信息，包括请求参数、响应结果和错误信息
    """

    def on_before_invoke(
        self,
        llm_instance: AIModelImpl,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ) -> None:
        """
        LLM调用前的回调函数

        记录模型调用的详细参数信息，包括模型名称、参数、工具、提示消息等

        :param llm_instance: LLM实例
        :param model: 模型名称
        :param credentials: 模型凭证信息
        :param prompt_messages: 提示消息列表
        :param model_parameters: 模型参数
        :param tools: 工具调用列表（可选）
        :param stop: 停止词列表（可选）
        :param stream: 是否流式响应
        :param user: 用户唯一标识（可选）
        """
        self.print_text("\n[on_llm_before_invoke]\n", color="blue")
        self.print_text(f"Model: {model}\n", color="blue")
        self.print_text("Parameters:\n", color="blue")
        for key, value in model_parameters.items():
            self.print_text(f"\t{key}: {value}\n", color="blue")

        if stop:
            self.print_text(f"\tstop: {stop}\n", color="blue")

        if tools:
            self.print_text("\tTools:\n", color="blue")
            for tool in tools:
                self.print_text(f"\t\t{tool.name}\n", color="blue")

        self.print_text(f"Stream: {stream}\n", color="blue")

        if user:
            self.print_text(f"User: {user}\n", color="blue")

        self.print_text("Prompt messages:\n", color="blue")
        for prompt_message in prompt_messages:
            if prompt_message.name:
                self.print_text(f"\tname: {prompt_message.name}\n", color="blue")

            self.print_text(f"\trole: {prompt_message.role.value}\n", color="blue")
            self.print_text(f"\tcontent: {prompt_message.content}\n", color="blue")

        if stream:
            self.print_text("\n[on_llm_new_chunk]")

    def on_new_chunk(
        self,
        llm_instance: AIModelImpl,
        chunk: LLMResultChunk,
        model: str,
        credentials: dict,
        prompt_messages: Sequence[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ):
        """
        接收到新数据块时的回调函数

        在流式响应模式下，每接收到一个新的数据块时调用此函数，用于实时输出生成的内容

        :param llm_instance: LLM实例
        :param chunk: 数据块
        :param model: 模型名称
        :param credentials: 模型凭证信息
        :param prompt_messages: 提示消息列表
        :param model_parameters: 模型参数
        :param tools: 工具调用列表（可选）
        :param stop: 停止词列表（可选）
        :param stream: 是否流式响应
        :param user: 用户唯一标识（可选）
        """
        # 实时输出流式响应的内容到标准输出
        sys.stdout.write(cast(str, chunk.delta.message.content))
        sys.stdout.flush()

    def on_after_invoke(
        self,
        llm_instance: AIModelImpl,
        result: LLMResult,
        model: str,
        credentials: dict,
        prompt_messages: Sequence[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ) -> None:
        """
        LLM调用完成后的回调函数

        记录模型调用的完整结果，包括生成的内容、工具调用、使用统计等信息

        :param llm_instance: LLM实例
        :param result: 调用结果
        :param model: 模型名称
        :param credentials: 模型凭证信息
        :param prompt_messages: 提示消息列表
        :param model_parameters: 模型参数
        :param tools: 工具调用列表（可选）
        :param stop: 停止词列表（可选）
        :param stream: 是否流式响应
        :param user: 用户唯一标识（可选）
        """
        self.print_text("\n[on_llm_after_invoke]\n", color="yellow")
        self.print_text(f"Content: {result.message.content}\n", color="yellow")

        # 如果有工具调用，输出工具调用信息
        if result.message.tool_calls:
            self.print_text("Tool calls:\n", color="yellow")
            for tool_call in result.message.tool_calls:
                self.print_text(f"\t{tool_call.id}\n", color="yellow")
                self.print_text(f"\t{tool_call.function.name}\n", color="yellow")
                self.print_text(
                    f"\t{json.dumps(tool_call.function.arguments)}\n", color="yellow"
                )

        self.print_text(f"Model: {result.model}\n", color="yellow")
        self.print_text(f"Usage: {result.usage}\n", color="yellow")  # 使用统计信息
        self.print_text(
            f"System Fingerprint: {result.system_fingerprint}\n", color="yellow"
        )

    def on_invoke_error(
        self,
        llm_instance: AIModelImpl,
        ex: Exception,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ) -> None:
        """
        LLM调用出错时的回调函数

        记录模型调用过程中发生的异常信息，用于调试和错误追踪

        :param llm_instance: LLM实例
        :param ex: 异常对象
        :param model: 模型名称
        :param credentials: 模型凭证信息
        :param prompt_messages: 提示消息列表
        :param model_parameters: 模型参数
        :param tools: 工具调用列表（可选）
        :param stop: 停止词列表（可选）
        :param stream: 是否流式响应
        :param user: 用户唯一标识（可选）
        """
        self.print_text("\n[on_llm_invoke_error]\n", color="red")
        _logger.exception(ex)  # 记录异常的详细信息和堆栈跟踪
