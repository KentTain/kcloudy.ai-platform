"""默认配置的参数设置."""

from pathlib import Path

from pydantic import Field

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.models.llm_config import LLMConfig


class SummarizeDescriptionsConfig(LLMConfig):
    """描述摘要的配置部分."""

    prompt: str | None = Field(description="要使用的描述摘要提示词。", default=None)
    max_length: int = Field(
        description="描述摘要的最大长度。",
        default=defs.SUMMARIZE_DESCRIPTIONS_MAX_LENGTH,
    )
    strategy: dict | None = Field(description="要使用的覆盖策略。", default=None)

    def resolved_strategy(self, root_dir: str) -> dict:
        """获取解析后的描述摘要策略."""
        from ai.components.graphrag.index.verbs.entities.summarize import (
            SummarizeStrategyType,
        )

        return self.strategy or {
            "type": SummarizeStrategyType.graph_intelligence,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "summarize_prompt": (Path(root_dir) / self.prompt)
            .read_bytes()
            .decode(encoding="utf-8")
            if self.prompt
            else None,
            "max_summary_length": self.max_length,
        }
