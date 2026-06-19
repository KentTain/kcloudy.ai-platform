"""
创建 OpenAI API 请求限流器的工厂函数

提供了根据配置创建 TPM/RPM 限流器的便捷方法。
"""

import logging

from aiolimiter import AsyncLimiter

from ai.components.graphrag.llm.limiting.llm_limiter import LLMLimiter
from ai.components.graphrag.llm.limiting.tpm_rpm_limiter import TpmRpmLLMLimiter
from ai.components.graphrag.llm.types import LLMConfig

log = logging.getLogger(__name__)


def create_tpm_rpm_limiters(
    configuration: LLMConfig,
) -> LLMLimiter:
    """
    根据配置创建 TPM/RPM 限流器

    从 LLMConfig 中读取 TPM 和 RPM 配置,创建相应的限流器。
    如果配置值为 0,则不创建该类型的限流器。

    Args:
        configuration: LLM 配置对象,包含 tokens_per_minute 和 requests_per_minute

    Returns
    -------
        配置好的 TpmRpmLLMLimiter 实例

    默认值:
        - TPM (tokens_per_minute): 50,000(如果未配置或为 None)
        - RPM (requests_per_minute): 10,000(如果未配置或为 None)
    """
    tpm = configuration.tokens_per_minute
    rpm = configuration.requests_per_minute
    return TpmRpmLLMLimiter(
        None if tpm == 0 else AsyncLimiter(tpm or 50_000),
        None if rpm == 0 else AsyncLimiter(rpm or 10_000),
    )
