# tests/extended/langchain/callbacks/processors/test_source_processor.py
import pytest
from extended.langchain.callbacks.processors.source_processor import SourceProcessor
from extended.langchain.callbacks.processors.base import ProcessContext
from ai.controllers.v1.chat.event_types import EventType

@pytest.mark.asyncio
class TestSourceProcessor:
    async def test_extract_url_sources_from_search_tool(self):
        """测试从搜索工具提取 URL 来源"""
        processor = SourceProcessor()
        context = ProcessContext(
            tool_name="google_search",
            tool_result={
                "results": [
                    {
                        "type": "url",
                        "url": "https://example.com",
                        "title": "Example",
                    }
                ]
            }
        )

        events = []
        async for event in processor.process(context):
            events.append(event)

        assert len(events) == 1
        assert events[0]["type"] == EventType.SOURCE_URL
        assert events[0]["url"] == "https://example.com"
        assert events[0]["title"] == "Example"

    async def test_extract_document_sources(self):
        """测试提取文档来源"""
        processor = SourceProcessor()
        context = ProcessContext(
            tool_name="web_search",
            tool_result={
                "results": [
                    {
                        "type": "document",
                        "url": "https://example.com/doc.pdf",
                        "title": "Document",
                        "mediaType": "application/pdf",
                    }
                ]
            }
        )

        events = []
        async for event in processor.process(context):
            events.append(event)

        assert len(events) == 1
        assert events[0]["type"] == EventType.SOURCE_DOCUMENT
        assert events[0]["mediaType"] == "application/pdf"

    async def test_non_search_tool_ignored(self):
        """测试非搜索工具被忽略"""
        processor = SourceProcessor()
        context = ProcessContext(
            tool_name="calculator",
            tool_result={"result": 42}
        )

        events = []
        async for event in processor.process(context):
            events.append(event)

        assert len(events) == 0

    async def test_supported_types(self):
        """测试支持的类型"""
        assert SourceProcessor.supported_types() == ["source-url", "source-document"]
