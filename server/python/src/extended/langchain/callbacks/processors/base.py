# src/extended/langchain/callbacks/processors/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Any

@dataclass
class ProcessContext:
    """处理器上下文"""
    tool_name: str | None = None
    tool_result: Any = None
    data: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

class UIPartProcessor(ABC):
    """UI Part 处理器基类"""

    @abstractmethod
    async def process(self, context: ProcessContext) -> AsyncGenerator[dict, None]:
        """处理并生成 SSE 事件

        Args:
            context: 处理器上下文

        Yields:
            SSE 事件字典
        """
        pass

    @classmethod
    @abstractmethod
    def supported_types(cls) -> list[str]:
        """返回此处理器支持的 Part 类型"""
        pass
