"""LLM 参数模型."""

from pydantic import BaseModel, ConfigDict, Field

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.enums import LLMType


class LLMParameters(BaseModel):
    """LLM 参数模型."""

    model_config = ConfigDict(protected_namespaces=(), extra="allow")
    api_key: str | None = Field(
        description="用于 LLM 服务的 API 密钥。",
        default=None,
    )
    type: LLMType = Field(description="要使用的 LLM 模型类型。", default=defs.LLM_TYPE)
    model: str = Field(description="要使用的 LLM 模型。", default=defs.LLM_MODEL)
    max_tokens: int | None = Field(
        description="要生成的最大 token 数量。",
        default=defs.LLM_MAX_TOKENS,
    )
    temperature: float | None = Field(
        description="用于 token 生成的温度。",
        default=defs.LLM_TEMPERATURE,
    )
    top_p: float | None = Field(
        description="用于 token 生成的 top-p 值。",
        default=defs.LLM_TOP_P,
    )
    n: int | None = Field(
        description="要生成的完成数量。",
        default=defs.LLM_N,
    )
    request_timeout: float = Field(
        description="要使用的请求超时。", default=defs.LLM_REQUEST_TIMEOUT
    )
    api_base: str | None = Field(description="LLM API 的基础 URL。", default=None)
    api_version: str | None = Field(description="要使用的 LLM API 版本。", default=None)
    organization: str | None = Field(description="用于 LLM 服务的组织。", default=None)
    proxy: str | None = Field(description="用于 LLM 服务的代理。", default=None)
    cognitive_services_endpoint: str | None = Field(
        description="认知服务的端点。", default=None
    )
    deployment_name: str | None = Field(
        description="用于 LLM 服务的部署名称。", default=None
    )
    model_supports_json: bool | None = Field(
        description="模型是否支持 JSON 输出模式。", default=None
    )
    tokens_per_minute: int = Field(
        description="用于 LLM 服务的每分钟 token 数量。",
        default=defs.LLM_TOKENS_PER_MINUTE,
    )
    requests_per_minute: int = Field(
        description="用于 LLM 服务的每分钟请求数量。",
        default=defs.LLM_REQUESTS_PER_MINUTE,
    )
    max_retries: int = Field(
        description="用于 LLM 服务的最大重试次数。",
        default=defs.LLM_MAX_RETRIES,
    )
    max_retry_wait: float = Field(
        description="用于 LLM 服务的最大重试等待时间。",
        default=defs.LLM_MAX_RETRY_WAIT,
    )
    sleep_on_rate_limit_recommendation: bool = Field(
        description="是否在速率限制建议时休眠。",
        default=defs.LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION,
    )
    concurrent_requests: int = Field(
        description="用于 LLM 服务的并发请求数量。",
        default=defs.LLM_CONCURRENT_REQUESTS,
    )
