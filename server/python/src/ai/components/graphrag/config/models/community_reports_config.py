"""默认配置的参数设置."""

from pathlib import Path

from pydantic import Field

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.models.llm_config import LLMConfig


class CommunityReportsConfig(LLMConfig):
    """社区报告的配置部分."""

    prompt: str | None = Field(description="要使用的社区报告提取提示词。", default=None)
    max_length: int = Field(
        description="社区报告的最大长度（以 token 为单位）。",
        default=defs.COMMUNITY_REPORT_MAX_LENGTH,
    )
    max_input_length: int = Field(
        description="生成报告时使用的最大输入长度（以 token 为单位）。",
        default=defs.COMMUNITY_REPORT_MAX_INPUT_LENGTH,
    )
    strategy: dict | None = Field(description="要使用的覆盖策略。", default=None)

    def resolved_strategy(self, root_dir) -> dict:
        """获取解析后的社区报告提取策略."""
        from ai.components.graphrag.index.verbs.graph.report import (
            CreateCommunityReportsStrategyType,
        )

        return self.strategy or {
            "type": CreateCommunityReportsStrategyType.graph_intelligence,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "extraction_prompt": (Path(root_dir) / self.prompt)
            .read_bytes()
            .decode(encoding="utf-8")
            if self.prompt
            else None,
            "max_report_length": self.max_length,
            "max_input_length": self.max_input_length,
        }
