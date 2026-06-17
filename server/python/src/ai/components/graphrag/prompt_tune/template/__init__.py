"""实体抽取,实体摘要和社区报告摘要的微调提示词模板。

Fine-tuning prompts for entity extraction, entity summarization, and community report summarization.
"""

from ai.components.graphrag.prompt_tune.template.community_report_summarization import (
    COMMUNITY_REPORT_SUMMARIZATION_PROMPT,
)
from ai.components.graphrag.prompt_tune.template.entity_extraction import (
    EXAMPLE_EXTRACTION_TEMPLATE,
    GRAPH_EXTRACTION_JSON_PROMPT,
    GRAPH_EXTRACTION_PROMPT,
    UNTYPED_EXAMPLE_EXTRACTION_TEMPLATE,
    UNTYPED_GRAPH_EXTRACTION_PROMPT,
)
from ai.components.graphrag.prompt_tune.template.entity_summarization import (
    ENTITY_SUMMARIZATION_PROMPT,
)

__all__ = [
    "COMMUNITY_REPORT_SUMMARIZATION_PROMPT",
    "ENTITY_SUMMARIZATION_PROMPT",
    "EXAMPLE_EXTRACTION_TEMPLATE",
    "GRAPH_EXTRACTION_JSON_PROMPT",
    "GRAPH_EXTRACTION_PROMPT",
    "UNTYPED_EXAMPLE_EXTRACTION_TEMPLATE",
    "UNTYPED_GRAPH_EXTRACTION_PROMPT",
]
