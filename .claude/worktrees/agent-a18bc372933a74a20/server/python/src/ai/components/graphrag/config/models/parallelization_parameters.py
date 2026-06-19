"""LLM 参数模型."""

from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs


class ParallelizationParameters(BaseModel):
    """并行化参数模型."""

    stagger: float = Field(
        description="用于 LLM 服务的交错时间。",
        default=defs.PARALLELIZATION_STAGGER,
    )
    num_threads: int = Field(
        description="用于 LLM 服务的线程数量。",
        default=defs.PARALLELIZATION_NUM_THREADS,
    )
