# tests/extended/langchain/callbacks/processors/test_registry.py
import pytest
from extended.langchain.callbacks.processors.base import UIPartProcessor, ProcessContext
from extended.langchain.callbacks.processors.registry import UIPartProcessorRegistry

class MockProcessor(UIPartProcessor):
    """模拟处理器"""

    @classmethod
    def supported_types(cls) -> list[str]:
        return ["mock-type"]

    async def process(self, context: ProcessContext):
        yield {"type": "mock-event"}

class TestProcessorRegistry:
    def test_registry_initialization(self):
        """测试注册中心初始化"""
        registry = UIPartProcessorRegistry()
        assert registry.processors == {}

    def test_register_processor(self):
        """测试注册处理器"""
        registry = UIPartProcessorRegistry()
        processor = MockProcessor()

        registry.register(processor)

        assert "mock-type" in registry.processors
        assert registry.processors["mock-type"] == processor

    def test_get_processor_by_type(self):
        """测试按类型获取处理器"""
        registry = UIPartProcessorRegistry()
        processor = MockProcessor()
        registry.register(processor)

        retrieved = registry.get_processor("mock-type")

        assert retrieved == processor
