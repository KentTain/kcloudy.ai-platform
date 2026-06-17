"""包含 'SummarizedDescriptionResult' 模型的模块."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from datashaper import VerbCallbacks

from ai.components.graphrag.index.cache import PipelineCache

StrategyConfig = dict[str, Any]


@dataclass
class SummarizedDescriptionResult:
    """封装组件图谱检索增强生成中的SummarizedDescriptionResult逻辑。"""

    items: str | tuple[str, str]
    description: str


SummarizationStrategy = Callable[
    [
        str | tuple[str, str],
        list[str],
        VerbCallbacks,
        PipelineCache,
        StrategyConfig,
    ],
    Awaitable[SummarizedDescriptionResult],
]
