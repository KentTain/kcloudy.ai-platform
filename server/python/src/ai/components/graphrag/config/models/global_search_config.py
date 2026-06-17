"""默认配置的参数设置."""

from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs


class GlobalSearchConfig(BaseModel):
    """缓存的默认配置部分."""

    temperature: float | None = Field(
        description="用于 token 生成的温度。",
        default=defs.GLOBAL_SEARCH_LLM_TEMPERATURE,
    )
    top_p: float | None = Field(
        description="用于 token 生成的 top-p 值。",
        default=defs.GLOBAL_SEARCH_LLM_TOP_P,
    )
    n: int | None = Field(
        description="要生成的完成数量。",
        default=defs.GLOBAL_SEARCH_LLM_N,
    )
    max_tokens: int = Field(
        description="最大上下文大小（以 token 为单位）。",
        default=defs.GLOBAL_SEARCH_MAX_TOKENS,
    )
    data_max_tokens: int = Field(
        description="数据 LLM 最大 token 数。",
        default=defs.GLOBAL_SEARCH_DATA_MAX_TOKENS,
    )
    map_max_tokens: int = Field(
        description="映射 LLM 最大 token 数。",
        default=defs.GLOBAL_SEARCH_MAP_MAX_TOKENS,
    )
    reduce_max_tokens: int = Field(
        description="归约 LLM 最大 token 数。",
        default=defs.GLOBAL_SEARCH_REDUCE_MAX_TOKENS,
    )
    concurrency: int = Field(
        description="并发请求数量。",
        default=defs.GLOBAL_SEARCH_CONCURRENCY,
    )
