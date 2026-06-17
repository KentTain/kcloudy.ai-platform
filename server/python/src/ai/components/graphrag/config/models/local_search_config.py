"""默认配置的参数设置."""

from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs


class LocalSearchConfig(BaseModel):
    """缓存的默认配置部分."""

    text_unit_prop: float = Field(
        description="文本单元比例。",
        default=defs.LOCAL_SEARCH_TEXT_UNIT_PROP,
    )
    community_prop: float = Field(
        description="社区比例。",
        default=defs.LOCAL_SEARCH_COMMUNITY_PROP,
    )
    conversation_history_max_turns: int = Field(
        description="对话历史最大轮数。",
        default=defs.LOCAL_SEARCH_CONVERSATION_HISTORY_MAX_TURNS,
    )
    top_k_entities: int = Field(
        description="top k 映射实体。",
        default=defs.LOCAL_SEARCH_TOP_K_MAPPED_ENTITIES,
    )
    top_k_relationships: int = Field(
        description="top k 映射关系。",
        default=defs.LOCAL_SEARCH_TOP_K_RELATIONSHIPS,
    )
    temperature: float | None = Field(
        description="用于 token 生成的温度。",
        default=defs.LOCAL_SEARCH_LLM_TEMPERATURE,
    )
    top_p: float | None = Field(
        description="用于 token 生成的 top-p 值。",
        default=defs.LOCAL_SEARCH_LLM_TOP_P,
    )
    n: int | None = Field(
        description="要生成的完成数量。",
        default=defs.LOCAL_SEARCH_LLM_N,
    )
    max_tokens: int = Field(
        description="最大 token 数。", default=defs.LOCAL_SEARCH_MAX_TOKENS
    )
    llm_max_tokens: int = Field(
        description="LLM 最大 token 数。", default=defs.LOCAL_SEARCH_LLM_MAX_TOKENS
    )
