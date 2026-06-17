"""默认配置的参数化设置."""

from typing import NotRequired

from ai.components.graphrag.config.input_models.llm_config_input import LLMConfigInput


class SummarizeDescriptionsConfigInput(LLMConfigInput):
    """描述摘要的配置部分."""

    prompt: NotRequired[str | None]
    max_length: NotRequired[int | str | None]
    strategy: NotRequired[dict | None]
