# tests/extended/langchain/callbacks/processors/test_file_processor.py
import pytest
from extended.langchain.callbacks.processors.file_processor import FileProcessor
from extended.langchain.callbacks.processors.base import ProcessContext
from ai.controllers.v1.chat.event_types import EventType

@pytest.mark.asyncio
class TestFileProcessor:
    async def test_extract_file_from_tool_result(self):
        """测试从工具结果提取文件"""
        processor = FileProcessor()
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
            }
        )

        events = []
        async for event in processor.process(context):
            events.append(event)

        assert len(events) == 2  # FILE_UPLOAD_START + FILE_UPLOAD_END
        assert events[0]["type"] == EventType.FILE_UPLOAD_START
        assert events[1]["type"] == EventType.FILE_UPLOAD_END
        assert events[1]["mediaType"] == "application/pdf"
        assert events[1]["filename"] == "report.pdf"

    async def test_non_file_tool_ignored(self):
        """测试非文件工具被忽略"""
        processor = FileProcessor()
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
        assert FileProcessor.supported_types() == ["file"]
