"""
LLM 调用结果类型定义

定义了 LLM 调用结果的数据结构。
"""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class LLMInvocationResult(Generic[T]):
    """
    LLM 调用结果

    包含了 LLM 调用的完整信息,包括结果,性能指标和 token 使用情况。
    """

    result: T | None
    """LLM 调用的结果数据"""

    name: str
    """操作名称"""

    num_retries: int
    """调用重试的次数"""

    total_time: float
    """LLM 调用的总时间(秒)"""

    call_times: list[float]
    """各次调用的网络耗时列表(秒)"""

    input_tokens: int
    """输入 token 数量"""

    output_tokens: int
    """输出 token 数量"""
