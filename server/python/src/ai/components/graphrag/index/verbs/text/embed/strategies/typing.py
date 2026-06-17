"""包含 'TextEmbeddingResult' 模型的模块."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from datashaper import VerbCallbacks

from ai.components.graphrag.index.cache import PipelineCache


@dataclass
class TextEmbeddingResult:
    """封装组件图谱检索增强生成中的TextEmbeddingResult逻辑。"""

    embeddings: list[list[float] | None] | None


TextEmbeddingStrategy = Callable[
    [
        list[str],
        VerbCallbacks,
        PipelineCache,
        dict,
    ],
    Awaitable[TextEmbeddingResult],
]
