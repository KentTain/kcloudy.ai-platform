"""默认配置的参数化设置."""

from typing import NotRequired

from datashaper import AsyncType
from typing_extensions import TypedDict

from ai.components.graphrag.config.input_models.llm_parameters_input import (
    LLMParametersInput,
)
from ai.components.graphrag.config.input_models.parallelization_parameters_input import (
    ParallelizationParametersInput,
)


class LLMConfigInput(TypedDict):
    """LLM配置步骤的基类."""

    llm: NotRequired[LLMParametersInput | None]
    parallelization: NotRequired[ParallelizationParametersInput | None]
    async_mode: NotRequired[AsyncType | str | None]
