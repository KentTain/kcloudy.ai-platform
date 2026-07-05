"""AI SDK 扩展集成测试

测试完整的 SSE 事件流，验证所有处理器协同工作。
"""

import asyncio

import pytest

from ai.controllers.v1.chat.event_types import EventType
from ai.controllers.v1.chat.llm import _sse_generator
from extended.langchain.callbacks.processors.base import ProcessContext
from extended.langchain.callbacks.processors.data_processor import DataProcessor
from extended.langchain.callbacks.processors.file_processor import FileProcessor
from extended.langchain.callbacks.processors.registry import UIPartProcessorRegistry
from extended.langchain.callbacks.processors.source_processor import SourceProcessor


@pytest.mark.asyncio
class TestAISDKExtensionIntegration:
    """AI SDK 扩展集成测试"""

    async def test_complete_event_flow_with_all_processors(self):
        """测试完整事件流（所有处理器）"""
        # 注册处理器
        registry = UIPartProcessorRegistry()
        registry.register(SourceProcessor())
        registry.register(FileProcessor())
        registry.register(DataProcessor())

        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        # 模拟搜索工具返回 URL 来源
        source_processor = registry.get_processor("source-url")
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
            },
        )

        async for event in source_processor.process(context):
            await event_queue.put(event)

        # 模拟文件工具返回文件
        file_processor = registry.get_processor("file")
        context = ProcessContext(
            tool_name="document_processor",
            tool_result={
                "files": [
                    {
                        "media_type": "application/pdf",
                        "url": "https://minio.example.com/doc.pdf",
                        "filename": "report.pdf",
                        "size": 1048576,
                    }
                ]
            },
        )

        async for event in file_processor.process(context):
            await event_queue.put(event)

        # 模拟数据工具返回表格
        data_processor = registry.get_processor("table")
        context = ProcessContext(
            tool_name="data_analyzer",
            tool_result={
                "type": "table",
                "data": {"headers": ["Name", "Age"], "rows": [["Alice", 25]]},
            },
        )

        async for event in data_processor.process(context):
            await event_queue.put(event)

        # 添加文本和结束事件
        await event_queue.put(
            {
                "type": EventType.TEXT_DELTA,
                "id": "text-123",
                "delta": "AI 回复内容",
            }
        )
        await event_queue.put(
            {
                "type": EventType.FINISH,
                "finishReason": "stop",
                "usage": {"promptTokens": 10, "completionTokens": 20},
            }
        )
        await event_queue.put(None)

        # 收集 SSE 输出
        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证所有事件类型都存在
        assert any("source-url" in line for line in outputs)
        assert any("file-upload-start" in line for line in outputs)
        assert any("file-upload-end" in line for line in outputs)
        assert any('"type":"data"' in line for line in outputs)
        assert any("text-delta" in line for line in outputs)
        assert any('"type":"finish"' in line for line in outputs)

    async def test_processor_registry_integration(self):
        """测试处理器注册中心集成"""
        registry = UIPartProcessorRegistry()

        # 注册所有处理器
        registry.register(SourceProcessor())
        registry.register(FileProcessor())
        registry.register(DataProcessor())

        # 验证可以按类型获取处理器
        assert registry.get_processor("source-url") is not None
        assert registry.get_processor("source-document") is not None
        assert registry.get_processor("file") is not None
        assert registry.get_processor("table") is not None
        assert registry.get_processor("json") is not None

    async def test_source_processor_with_sse_generator(self):
        """测试 SourceProcessor + SSE Generator 集成"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        source_processor = SourceProcessor()
        context = ProcessContext(
            tool_name="web_search",
            tool_result={
                "results": [
                    {
                        "type": "document",
                        "url": "https://example.com/paper.pdf",
                        "title": "Research Paper",
                        "mediaType": "application/pdf",
                    }
                ]
            },
        )

        async for event in source_processor.process(context):
            await event_queue.put(event)

        await event_queue.put(
            {
                "type": EventType.FINISH,
                "finishReason": "stop",
                "usage": {"promptTokens": 5, "completionTokens": 10},
            }
        )
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        assert any("source-document" in line for line in outputs)
        assert any("application/pdf" in line for line in outputs)

    async def test_file_processor_integration(self):
        """测试 FileProcessor 集成"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        file_processor = FileProcessor()
        context = ProcessContext(
            tool_name="document_upload",
            tool_result={
                "files": [
                    {
                        "media_type": "image/png",
                        "url": "https://minio.example.com/image.png",
                        "filename": "screenshot.png",
                        "size": 204800,
                    }
                ]
            },
        )

        async for event in file_processor.process(context):
            await event_queue.put(event)

        await event_queue.put(
            {
                "type": EventType.FINISH,
                "finishReason": "stop",
                "usage": {"promptTokens": 3, "completionTokens": 7},
            }
        )
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证文件上传事件序列
        assert any("file-upload-start" in line for line in outputs)
        assert any("file-upload-end" in line for line in outputs)
        assert any("image/png" in line for line in outputs)
        assert any("screenshot.png" in line for line in outputs)

    async def test_data_processor_integration(self):
        """测试 DataProcessor 集成"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        data_processor = DataProcessor()
        context = ProcessContext(
            tool_name="data_query",
            tool_result={
                "type": "json",
                "data": {"name": "Alice", "age": 25, "city": "Beijing"},
            },
        )

        async for event in data_processor.process(context):
            await event_queue.put(event)

        await event_queue.put(
            {
                "type": EventType.FINISH,
                "finishReason": "stop",
                "usage": {"promptTokens": 8, "completionTokens": 15},
            }
        )
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证数据事件
        assert any('"type":"data"' in line for line in outputs)
        assert any('"dataType":"json"' in line for line in outputs)
        assert any("Alice" in line for line in outputs)

    async def test_multiple_sources_in_single_tool_call(self):
        """测试单个工具调用返回多个来源"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        source_processor = SourceProcessor()
        context = ProcessContext(
            tool_name="search_tool",
            tool_result={
                "results": [
                    {
                        "type": "url",
                        "url": "https://example1.com",
                        "title": "Example 1",
                    },
                    {
                        "type": "url",
                        "url": "https://example2.com",
                        "title": "Example 2",
                    },
                    {
                        "type": "document",
                        "url": "https://example3.com/doc.pdf",
                        "title": "Document",
                        "mediaType": "application/pdf",
                    },
                ]
            },
        )

        async for event in source_processor.process(context):
            await event_queue.put(event)

        await event_queue.put(
            {
                "type": EventType.FINISH,
                "finishReason": "stop",
                "usage": {"promptTokens": 10, "completionTokens": 10},
            }
        )
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证所有来源都被处理
        source_url_count = sum(1 for line in outputs if "source-url" in line)
        source_doc_count = sum(1 for line in outputs if "source-document" in line)

        assert source_url_count >= 2  # 至少 2 个 URL 来源
        assert source_doc_count >= 1  # 至少 1 个文档来源

    async def test_sse_event_format_compliance(self):
        """测试 SSE 事件格式合规性"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        # 添加各种类型的事件
        await event_queue.put(
            {
                "type": EventType.SOURCE_URL,
                "sourceId": "source-123",
                "url": "https://example.com",
                "title": "Example",
            }
        )

        await event_queue.put(
            {
                "type": EventType.TEXT_DELTA,
                "id": "text-123",
                "delta": "Test content",
            }
        )

        await event_queue.put(
            {
                "type": EventType.FINISH,
                "finishReason": "stop",
                "usage": {"promptTokens": 5, "completionTokens": 10},
            }
        )
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证 SSE 格式
        for line in outputs:
            assert line.startswith("data: ") or line == "data: [DONE]\n\n"
            assert line.endswith("\n\n")

        # 验证事件包含必要字段
        assert any('"type":"start"' in line for line in outputs)
        assert any('"messageId":"test-message-id"' in line for line in outputs)
        assert any('"type":"finish"' in line for line in outputs)

    async def test_event_ordering_with_mixed_types(self):
        """测试混合事件类型的顺序处理"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        # 按特定顺序添加不同类型的事件
        events = [
            {"type": EventType.SOURCE_URL, "sourceId": "source-1", "url": "https://example.com"},
            {"type": EventType.FILE_UPLOAD_START, "fileId": "file-1"},
            {
                "type": EventType.FILE_UPLOAD_END,
                "fileId": "file-1",
                "mediaType": "application/pdf",
                "url": "https://example.com/file.pdf",
            },
            {"type": EventType.TEXT_DELTA, "id": "text-1", "delta": "Content"},
            {"type": EventType.DATA, "dataId": "data-1", "dataType": "json", "content": {}},
            {"type": EventType.FINISH, "finishReason": "stop", "usage": {}},
        ]

        for event in events:
            await event_queue.put(event)
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证事件按添加顺序输出
        source_idx = next(i for i, line in enumerate(outputs) if "source-url" in line)
        file_start_idx = next(i for i, line in enumerate(outputs) if "file-upload-start" in line)
        file_end_idx = next(i for i, line in enumerate(outputs) if "file-upload-end" in line)
        text_idx = next(i for i, line in enumerate(outputs) if "text-delta" in line)
        data_idx = next(i for i, line in enumerate(outputs) if '"type":"data"' in line)
        finish_idx = next(i for i, line in enumerate(outputs) if '"type":"finish"' in line)

        assert source_idx < file_start_idx < file_end_idx < text_idx < data_idx < finish_idx
