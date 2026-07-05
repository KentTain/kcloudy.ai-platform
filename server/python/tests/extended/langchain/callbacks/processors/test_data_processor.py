# tests/extended/langchain/callbacks/processors/test_data_processor.py
import pytest
from extended.langchain.callbacks.processors.data_processor import DataProcessor
from extended.langchain.callbacks.processors.base import ProcessContext
from ai.controllers.v1.chat.event_types import EventType

@pytest.mark.asyncio
class TestDataProcessor:
    async def test_extract_table_data(self):
        """测试提取表格数据"""
        processor = DataProcessor()
        context = ProcessContext(
            tool_name="data_analyzer",
            tool_result={
                "type": "table",
                "data": {
                    "headers": ["Name", "Age"],
                    "rows": [["Alice", 25], ["Bob", 30]],
                }
            }
        )

        events = []
        async for event in processor.process(context):
            events.append(event)

        assert len(events) == 1
        assert events[0]["type"] == EventType.DATA
        assert events[0]["dataType"] == "table"
        assert events[0]["content"]["headers"] == ["Name", "Age"]

    async def test_extract_json_data(self):
        """测试提取 JSON 数据"""
        processor = DataProcessor()
        context = ProcessContext(
            tool_name="api_caller",
            tool_result={
                "type": "json",
                "data": {"key": "value", "nested": {"field": 123}}
            }
        )

        events = []
        async for event in processor.process(context):
            events.append(event)

        assert len(events) == 1
        assert events[0]["type"] == EventType.DATA
        assert events[0]["dataType"] == "json"

    async def test_non_data_tool_ignored(self):
        """测试非数据工具被忽略"""
        processor = DataProcessor()
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
        assert DataProcessor.supported_types() == ["table", "json"]
