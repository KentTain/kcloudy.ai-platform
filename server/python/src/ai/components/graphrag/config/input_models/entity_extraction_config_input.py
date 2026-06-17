"""默认配置的参数化设置."""

from typing import NotRequired

from ai.components.graphrag.config.input_models.llm_config_input import LLMConfigInput


class EntityExtractionConfigInput(LLMConfigInput):
    """实体提取的配置部分."""

    prompt: NotRequired[str | None]
    entity_types: NotRequired[list[str] | str | None]
    max_gleanings: NotRequired[int | str | None]
    strategy: NotRequired[dict | None]
    encoding_model: NotRequired[str | None]
