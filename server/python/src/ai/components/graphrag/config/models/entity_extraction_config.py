"""默认配置的参数设置."""

from pathlib import Path

from pydantic import Field

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.models.llm_config import LLMConfig


class EntityExtractionConfig(LLMConfig):
    """实体提取的配置部分."""

    prompt: str | None = Field(description="要使用的实体提取提示词。", default=None)
    entity_types: list[str] = Field(
        description="要使用的实体提取实体类型。",
        default=defs.ENTITY_EXTRACTION_ENTITY_TYPES,
    )
    max_gleanings: int = Field(
        description="要使用的最大实体收集数量。",
        default=defs.ENTITY_EXTRACTION_MAX_GLEANINGS,
    )
    strategy: dict | None = Field(description="覆盖默认实体提取策略", default=None)
    encoding_model: str | None = Field(default=None, description="要使用的编码模型。")

    def resolved_strategy(self, root_dir: str, encoding_model: str) -> dict:
        """获取解析后的实体提取策略."""
        from ai.components.graphrag.index.verbs.entities.extraction import (
            ExtractEntityStrategyType,
        )

        return self.strategy or {
            "type": ExtractEntityStrategyType.graph_intelligence,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "extraction_prompt": (Path(root_dir) / self.prompt)
            .read_bytes()
            .decode(encoding="utf-8")
            if self.prompt
            else None,
            "max_gleanings": self.max_gleanings,
            # 在 create_base_text_units 中已预分块
            "encoding_name": self.encoding_model or encoding_model,
            "prechunked": True,
        }
