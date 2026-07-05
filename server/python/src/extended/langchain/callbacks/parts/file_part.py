# src/extended/langchain/callbacks/parts/file_part.py
from dataclasses import dataclass, field
from typing import Literal, Optional, Any

@dataclass
class FilePart:
    """文件附件"""
    type: Literal["file"] = "file"
    media_type: str = ""
    url: str = ""
    filename: Optional[str] = None
    size: Optional[int] = None
    provider_metadata: Optional[dict[str, Any]] = None
