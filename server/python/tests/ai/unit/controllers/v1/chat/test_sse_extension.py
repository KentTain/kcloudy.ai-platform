"""SSE Generator 扩展事件测试

测试新事件类型的 SSE 流输出。
"""

import asyncio

import pytest

from ai.controllers.v1.chat.event_types import EventType
from ai.controllers.v1.chat.llm import _sse_generator


@pytest.mark.asyncio
class TestSSEExtension:
    """SSE 扩展事件测试"""

    async def test_source_url_event(self):
        """测试来源 URL 事件"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        await event_queue.put(
            {
                "type": EventType.SOURCE_URL,
                "sourceId": "source-123",
                "url": "https://example.com",
                "title": "Example",
            }
        )
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        assert any("source-url" in line for line in outputs)
        assert any("https://example.com" in line for line in outputs)

    async def test_source_document_event(self):
        """测试来源文档事件"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        await event_queue.put(
            {
                "type": EventType.SOURCE_DOCUMENT,
                "sourceId": "source-456",
                "filename": "document.pdf",
            }
        )
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        assert any("source-document" in line for line in outputs)
        assert any("document.pdf" in line for line in outputs)

    async def test_file_upload_events(self):
        """测试文件上传事件"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        await event_queue.put(
            {
                "type": EventType.FILE_UPLOAD_START,
                "fileId": "file-123",
            }
        )
        await event_queue.put(
            {
                "type": EventType.FILE_UPLOAD_END,
                "fileId": "file-123",
                "mediaType": "application/pdf",
                "url": "https://minio.example.com/doc.pdf",
                "filename": "document.pdf",
            }
        )
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        assert any("file-upload-start" in line for line in outputs)
        assert any("file-upload-end" in line for line in outputs)

    async def test_data_event(self):
        """测试数据事件"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        await event_queue.put(
            {
                "type": EventType.DATA,
                "dataId": "data-123",
                "dataType": "table",
                "content": {
                    "headers": ["Name", "Age"],
                    "rows": [["Alice", 25]],
                },
            }
        )
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        assert any('"type":"data"' in line for line in outputs)
        assert any("table" in line for line in outputs)

    async def test_warning_event(self):
        """测试警告事件"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        await event_queue.put(
            {
                "type": EventType.WARNING,
                "message": "Test warning",
            }
        )
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        assert any("warning" in line for line in outputs)
        assert any("Test warning" in line for line in outputs)
