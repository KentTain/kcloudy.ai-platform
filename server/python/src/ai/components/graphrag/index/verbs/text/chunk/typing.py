"""包含 'TextChunk' 模型的模块."""

from dataclasses import dataclass


@dataclass
class TextChunk:
    """封装组件图谱检索增强生成中的TextChunk逻辑。"""

    text_chunk: str
    source_doc_indices: list[int]
    n_tokens: int | None = None


ChunkInput = str | list[str] | list[tuple[str, str]]
"""Input to a chunking strategy. Can be a string, a list of strings, or a list of tuples of (id, text)."""
