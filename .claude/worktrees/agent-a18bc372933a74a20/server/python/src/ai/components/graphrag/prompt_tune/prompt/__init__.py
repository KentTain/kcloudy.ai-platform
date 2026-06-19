"""提示词生成相关的提示词定义模块。

Persona, entity type, relationships and domain generation prompts module.
"""

from ai.components.graphrag.prompt_tune.prompt.community_report_rating import (
    GENERATE_REPORT_RATING_PROMPT,
)
from ai.components.graphrag.prompt_tune.prompt.community_reporter_role import (
    GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT,
)
from ai.components.graphrag.prompt_tune.prompt.domain import GENERATE_DOMAIN_PROMPT
from ai.components.graphrag.prompt_tune.prompt.entity_relationship import (
    ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT,
    ENTITY_RELATIONSHIPS_GENERATION_PROMPT,
    UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT,
)
from ai.components.graphrag.prompt_tune.prompt.entity_types import (
    ENTITY_TYPE_GENERATION_JSON_PROMPT,
    ENTITY_TYPE_GENERATION_PROMPT,
)
from ai.components.graphrag.prompt_tune.prompt.language import DETECT_LANGUAGE_PROMPT
from ai.components.graphrag.prompt_tune.prompt.persona import GENERATE_PERSONA_PROMPT

__all__ = [
    "DETECT_LANGUAGE_PROMPT",
    "ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT",
    "ENTITY_RELATIONSHIPS_GENERATION_PROMPT",
    "ENTITY_TYPE_GENERATION_JSON_PROMPT",
    "ENTITY_TYPE_GENERATION_PROMPT",
    "GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT",
    "GENERATE_DOMAIN_PROMPT",
    "GENERATE_PERSONA_PROMPT",
    "GENERATE_REPORT_RATING_PROMPT",
    "UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT",
]
