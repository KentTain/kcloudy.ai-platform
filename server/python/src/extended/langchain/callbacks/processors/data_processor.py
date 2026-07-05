# src/extended/langchain/callbacks/processors/data_processor.py
import uuid
from typing import AsyncGenerator
from loguru import logger
from extended.langchain.callbacks.processors.base import UIPartProcessor, ProcessContext
from ai.controllers.v1.chat.event_types import EventType

_logger = logger.bind(name=__name__)

class DataProcessor(UIPartProcessor):
    """数据处理器"""

    DATA_TOOL_KEYWORDS = frozenset([
        "data", "analyze", "query", "database",
        "api", "fetch", "table", "chart"
    ])

    @classmethod
    def supported_types(cls) -> list[str]:
        return ["table", "json"]

    async def process(self, context: ProcessContext) -> AsyncGenerator[dict, None]:
        """处理工具调用结果，提取结构化数据"""
        if not context.tool_name or not context.tool_result:
            return

        if not self._is_data_tool(context.tool_name):
            return

        data_items = self._extract_data(context.tool_result)

        for data_item in data_items:
            try:
                yield {
                    "type": EventType.DATA,
                    "dataId": f"data-{uuid.uuid4().hex[:8]}",
                    "dataType": data_item["type"],
                    "content": data_item["content"],
                }
            except Exception as e:
                _logger.warning(f"Failed to create data event: {e}")

    def _is_data_tool(self, tool_name: str) -> bool:
        """判断是否是数据类工具"""
        if not tool_name:
            return False
        tool_name_lower = tool_name.lower()
        return any(keyword in tool_name_lower for keyword in self.DATA_TOOL_KEYWORDS)

    def _extract_data(self, tool_result) -> list[dict]:
        """从工具结果中提取数据"""
        data_items = []

        if isinstance(tool_result, dict):
            if "type" in tool_result and "data" in tool_result:
                data_type = tool_result["type"]
                if data_type in ["table", "json"]:
                    data_items.append({
                        "type": data_type,
                        "content": tool_result["data"],
                    })

            elif "headers" in tool_result and "rows" in tool_result:
                data_items.append({
                    "type": "table",
                    "content": {
                        "headers": tool_result["headers"],
                        "rows": tool_result["rows"],
                    },
                })

            elif not any(key in tool_result for key in ["result", "error", "files"]):
                data_items.append({
                    "type": "json",
                    "content": tool_result,
                })

        return data_items
