"""默认配置的参数设置."""

from datashaper import AsyncType
from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.models.llm_parameters import LLMParameters
from ai.components.graphrag.config.models.parallelization_parameters import (
    ParallelizationParameters,
)


class LLMConfig(BaseModel):
    """LLM 配置步骤的基类."""

    llm: LLMParameters = Field(
        description="要使用的 LLM 配置。", default=LLMParameters()
    )
    parallelization: ParallelizationParameters = Field(
        description="要使用的并行化配置。",
        default=ParallelizationParameters(),
    )
    async_mode: AsyncType = Field(
        description="要使用的异步模式。", default=defs.ASYNC_MODE
    )
