# src/extended/langchain/callbacks/parts/data_part.py
from dataclasses import dataclass, field
from typing import Any
import uuid

@dataclass
class DataPart:
    """自定义数据"""
    type: str  # "table" | "json"
    id: str = field(default_factory=lambda: f"data-{uuid.uuid4().hex[:8]}")
    content: Any = None
