"""包含 'TextTranslationResult' 模型的模块."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from datashaper import VerbCallbacks

from ai.components.graphrag.index.cache import PipelineCache


@dataclass
class TextTranslationResult:
    """封装组件图谱检索增强生成中的TextTranslationResult逻辑。"""

    translations: list[str]


TextTranslationStrategy = Callable[
    [list[str], dict[str, Any], VerbCallbacks, PipelineCache],
    Awaitable[TextTranslationResult],
]
