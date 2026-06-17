"""默认配置的参数设置."""

from pathlib import Path

from pydantic import Field

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.models.llm_config import LLMConfig


class ClaimExtractionConfig(LLMConfig):
    """声明提取的配置部分."""

    enabled: bool = Field(
        description="是否启用声明提取。",
    )
    prompt: str | None = Field(description="要使用的声明提取提示词。", default=None)
    description: str = Field(
        description="要使用的声明描述。",
        default=defs.CLAIM_DESCRIPTION,
    )
    max_gleanings: int = Field(
        description="要使用的最大实体收集数量。",
        default=defs.CLAIM_MAX_GLEANINGS,
    )
    strategy: dict | None = Field(description="要使用的覆盖策略。", default=None)
    encoding_model: str | None = Field(default=None, description="要使用的编码模型。")

    def resolved_strategy(self, root_dir: str, encoding_model: str) -> dict:
        """获取解析后的声明提取策略."""
        from ai.components.graphrag.index.verbs.covariates.extract_covariates import (
            ExtractClaimsStrategyType,
        )

        return self.strategy or {
            "type": ExtractClaimsStrategyType.graph_intelligence,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "extraction_prompt": (Path(root_dir) / self.prompt)
            .read_bytes()
            .decode(encoding="utf-8")
            if self.prompt
            else None,
            "claim_description": self.description,
            "max_gleanings": self.max_gleanings,
            "encoding_name": self.encoding_model or encoding_model,
        }
