# src/extended/langchain/callbacks/parts/source_part.py
from dataclasses import dataclass, field
from typing import Literal, Optional, Any
import uuid

@dataclass
class SourceUrlPart:
    """来源引用 - URL"""
    type: Literal["source-url"] = "source-url"
    source_id: str = field(default_factory=lambda: f"source-{uuid.uuid4().hex[:8]}")
    url: str = ""
    title: Optional[str] = None
    provider_metadata: Optional[dict[str, Any]] = None

@dataclass
class SourceDocumentPart:
    """来源引用 - 文档"""
    type: Literal["source-document"] = "source-document"
    source_id: str = field(default_factory=lambda: f"source-{uuid.uuid4().hex[:8]}")
    media_type: str = ""
    url: str = ""
    title: Optional[str] = None
    provider_metadata: Optional[dict[str, Any]] = None
