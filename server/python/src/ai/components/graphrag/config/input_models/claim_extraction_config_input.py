"""默认配置的参数化设置."""

from typing import NotRequired

from ai.components.graphrag.config.input_models.llm_config_input import LLMConfigInput


class ClaimExtractionConfigInput(LLMConfigInput):
    """声明提取的配置部分."""

    enabled: NotRequired[bool | None]
    prompt: NotRequired[str | None]
    description: NotRequired[str | None]
    max_gleanings: NotRequired[int | str | None]
    strategy: NotRequired[dict | None]
    encoding_model: NotRequired[str | None]
