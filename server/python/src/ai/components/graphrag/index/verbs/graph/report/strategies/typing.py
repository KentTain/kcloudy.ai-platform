"""包含 'Finding' and 'CommunityReport' 模型的模块."""

from collections.abc import Awaitable, Callable
from typing import Any

from datashaper import VerbCallbacks
from typing_extensions import TypedDict

from ai.components.graphrag.index.cache import PipelineCache

ExtractedEntity = dict[str, Any]
StrategyConfig = dict[str, Any]
RowContext = dict[str, Any]
EntityTypes = list[str]
Claim = dict[str, Any]


class Finding(TypedDict):
    """封装组件图谱检索增强生成中的Finding逻辑。"""

    summary: str
    explanation: str


class CommunityReport(TypedDict):
    """封装组件图谱检索增强生成中的CommunityReport逻辑。"""

    community: str | int
    title: str
    summary: str
    full_content: str
    full_content_json: str
    rank: float
    level: int
    rank_explanation: str
    findings: list[Finding]


CommunityReportsStrategy = Callable[
    [
        str | int,
        str,
        int,
        VerbCallbacks,
        PipelineCache,
        StrategyConfig,
    ],
    Awaitable[CommunityReport | None],
]
