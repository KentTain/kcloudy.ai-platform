"""
LLM 输入输出类型定义

定义了 LLM 调用的输入和输出数据结构。
"""

from dataclasses import dataclass, field
from typing import Generic, NotRequired, TypeVar

from typing_extensions import TypedDict

from ai.components.graphrag.llm.types.llm_callbacks import IsResponseValidFn


class LLMInput(TypedDict):
    """
    LLM 调用的输入参数

    定义了调用 LLM 时可以传递的所有可选参数。
    """

    name: NotRequired[str]
    """LLM 调用的名称(可选),用于日志记录和调试"""

    json: NotRequired[bool]
    """
    如果为 True,将尝试从 LLM 获取 JSON 输出
    解析后的 JSON 将在 `json_output` 字段中返回
    """

    is_response_valid: NotRequired[IsResponseValidFn]
    """
    用于检查 LLM 响应是否有效的函数(可选)
    仅在 `json=True` 时有效
    """

    variables: NotRequired[dict]
    """在提示词中使用的变量替换字典(可选)"""

    history: NotRequired[list[dict] | None]
    """LLM 调用的历史记录(可选),例如在聊天模式下使用"""

    model_parameters: NotRequired[dict]
    """在 LLM 调用中使用的额外模型参数(可选)"""


T = TypeVar("T")


@dataclass
class LLMOutput(Generic[T]):
    """
    LLM 调用的输出结果

    包含了 LLM 的输出数据以及相关的元信息。
    """

    output: T | None
    """LLM 调用的输出数据"""

    json: dict | None = field(default=None)
    """从 LLM 获取的 JSON 输出(如果可用)"""

    history: list[dict] | None = field(default=None)
    """LLM 调用的历史记录(如果可用),例如在聊天模式下"""
