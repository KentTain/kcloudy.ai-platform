"""
回调函数基类

迁移自 Alon: src/alon/components/model/callbacks/base_callback.py

提供 LLM 调用的回调机制基类
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.components.model.model_providers.__base__.ai_model import AIModelImpl
from ai_plugin.sdk.entities.model.llm import LLMResult, LLMResultChunk
from ai_plugin.sdk.entities.model.message import PromptMessage, PromptMessageTool


_TEXT_COLOR_MAPPING = {
    "blue": "36;1",
    "yellow": "33;1",
    "pink": "38;5;200",
    "green": "32;1",
    "red": "31;1",
}


class Callback(ABC):
    """
    回调函数基础类

    仅用于 LLM 调用的生命周期回调
    """

    raise_error: bool = False

    @abstractmethod
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
        调用前回调函数

        :param llm_instance: LLM 实例
        :param model: 模型名称
        :param credentials: 模型凭证
        :param prompt_messages: 提示消息
        :param model_parameters: 模型参数
        :param tools: 工具调用
        :param stop: 停止词
        :param stream: 是否流式响应
        :param user: 唯一用户 ID
        """
        raise NotImplementedError()

    @abstractmethod
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
        新块回调函数

        :param llm_instance: LLM 实例
        :param chunk: 数据块
        :param model: 模型名称
        :param credentials: 模型凭证
        :param prompt_messages: 提示消息
        :param model_parameters: 模型参数
        :param tools: 工具调用
        :param stop: 停止词
        :param stream: 是否流式响应
        :param user: 唯一用户 ID
        """
        raise NotImplementedError()

    @abstractmethod
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
        调用后回调函数

        :param llm_instance: LLM 实例
        :param result: 结果
        :param model: 模型名称
        :param credentials: 模型凭证
        :param prompt_messages: 提示消息
        :param model_parameters: 模型参数
        :param tools: 工具调用
        :param stop: 停止词
        :param stream: 是否流式响应
        :param user: 唯一用户 ID
        """
        raise NotImplementedError()

    @abstractmethod
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
        调用错误回调函数

        :param llm_instance: LLM 实例
        :param ex: 异常
        :param model: 模型名称
        :param credentials: 模型凭证
        :param prompt_messages: 提示消息
        :param model_parameters: 模型参数
        :param tools: 工具调用
        :param stop: 停止词
        :param stream: 是否流式响应
        :param user: 唯一用户 ID
        """
        raise NotImplementedError()

    def print_text(self, text: str, color: str | None = None, end: str = "") -> None:
        """打印带高亮且无结束字符的文本。"""
        text_to_print = self._get_colored_text(text, color) if color else text
        print(text_to_print, end=end)

    def _get_colored_text(self, text: str, color: str) -> str:
        """获取彩色文本。"""
        color_str = _TEXT_COLOR_MAPPING[color]
        return f"[{color_str}m\033[1;3m{text}[0m"
