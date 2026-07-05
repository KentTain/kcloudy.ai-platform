# src/extended/langchain/callbacks/processors/source_processor.py
import uuid
from typing import AsyncGenerator
from loguru import logger
from extended.langchain.callbacks.processors.base import UIPartProcessor, ProcessContext
from ai.controllers.v1.chat.event_types import EventType

_logger = logger.bind(name=__name__)

class SourceProcessor(UIPartProcessor):
    """来源引用处理器"""

    SEARCH_TOOL_KEYWORDS = frozenset([
        "search", "baidu", "google", "bing",
        "duckduckgo", "websearch", "web_search"
    ])

    @classmethod
    def supported_types(cls) -> list[str]:
        return ["source-url", "source-document"]

    async def process(self, context: ProcessContext) -> AsyncGenerator[dict, None]:
        """处理工具调用结果，提取来源信息"""
        if not context.tool_name or not context.tool_result:
            return

        if not self._is_search_tool(context.tool_name):
            return

        sources = self._extract_sources(context.tool_result)

        for source in sources:
            try:
                if source.get("type") == "url":
                    yield {
                        "type": EventType.SOURCE_URL,
                        "sourceId": source["source_id"],
                        "url": source["url"],
                        "title": source.get("title"),
                    }
                elif source.get("type") == "document":
                    yield {
                        "type": EventType.SOURCE_DOCUMENT,
                        "sourceId": source["source_id"],
                        "mediaType": source["media_type"],
                        "url": source["url"],
                        "title": source.get("title"),
                    }
            except Exception as e:
                _logger.warning(f"Failed to create source event: {e}")

    def _is_search_tool(self, tool_name: str) -> bool:
        """判断是否是搜索类工具"""
        if not tool_name:
            return False
        tool_name_lower = tool_name.lower()
        return any(keyword in tool_name_lower for keyword in self.SEARCH_TOOL_KEYWORDS)

    def _extract_sources(self, tool_result) -> list[dict]:
        """从工具结果中提取来源信息"""
        sources = []

        if isinstance(tool_result, dict):
            results = tool_result.get("results", [])
            if isinstance(results, list):
                for item in results:
                    if item.get("type") in ["url", "document"]:
                        sources.append({
                            "type": item["type"],
                            "source_id": f"source-{uuid.uuid4().hex[:8]}",
                            "url": item.get("url", ""),
                            "title": item.get("title"),
                            "media_type": item.get("mediaType", ""),
                        })

        return sources
