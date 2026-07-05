# src/extended/langchain/callbacks/processors/registry.py
from typing import Dict
from extended.langchain.callbacks.processors.base import UIPartProcessor

class UIPartProcessorRegistry:
    """UI Part 处理器注册中心"""

    def __init__(self):
        self.processors: Dict[str, UIPartProcessor] = {}

    def register(self, processor: UIPartProcessor) -> None:
        """注册处理器"""
        for part_type in processor.supported_types():
            self.processors[part_type] = processor

    def get_processor(self, part_type: str) -> UIPartProcessor | None:
        """获取处理器"""
        return self.processors.get(part_type)
