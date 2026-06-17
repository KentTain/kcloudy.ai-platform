# isort: skip_file
"""包含'PipelineRunStats'和'PipelineRunContext'模型的模块."""

from dataclasses import dataclass as dc_dataclass
from dataclasses import field

from ai.components.graphrag.index.cache import PipelineCache
from .storage.typing import PipelineStorage


@dc_dataclass
class PipelineRunStats:
    """流水线运行统计信息."""

    total_runtime: float = field(default=0)
    """表示总运行时间的浮点数."""

    num_documents: int = field(default=0)
    """文档数量."""

    input_load_time: float = field(default=0)
    """表示输入加载时间的浮点数."""

    workflows: dict[str, dict[str, float]] = field(default_factory=dict)
    """工作流字典."""


@dc_dataclass
class PipelineRunContext:
    """提供当前流水线运行的上下文."""

    stats: PipelineRunStats
    storage: PipelineStorage
    cache: PipelineCache


# TODO: 目前只是拥有相同的可用属性
VerbRunContext = PipelineRunContext
"""提供当前动词运行的上下文."""
