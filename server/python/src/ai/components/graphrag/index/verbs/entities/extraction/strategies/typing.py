"""包含 'Document' 和 'EntityExtractionResult' 模型的模块."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from datashaper import VerbCallbacks

from ai.components.graphrag.index.cache import PipelineCache

ExtractedEntity = dict[str, Any]
StrategyConfig = dict[str, Any]
EntityTypes = list[str]


@dataclass
class Document:
    """Document 类定义."""

    text: str
    id: str


@dataclass
class EntityExtractionResult:
    """实体提取结果类定义."""

    entities: list[ExtractedEntity]
    graphml_graph: str | None


EntityExtractStrategy = Callable[
    [
        list[Document],
        EntityTypes,
        VerbCallbacks,
        PipelineCache,
        StrategyConfig,
    ],
    Awaitable[EntityExtractionResult],
]
