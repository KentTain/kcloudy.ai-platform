"""默认配置的参数化设置."""

from typing import NotRequired

from ai.components.graphrag.config.enums import (
    TextEmbeddingTarget,
)
from ai.components.graphrag.config.input_models.llm_config_input import LLMConfigInput


class TextEmbeddingConfigInput(LLMConfigInput):
    """文本嵌入的配置部分."""

    batch_size: NotRequired[int | str | None]
    batch_max_tokens: NotRequired[int | str | None]
    target: NotRequired[TextEmbeddingTarget | str | None]
    skip: NotRequired[list[str] | str | None]
    vector_store: NotRequired[dict | None]
    strategy: NotRequired[dict | None]
