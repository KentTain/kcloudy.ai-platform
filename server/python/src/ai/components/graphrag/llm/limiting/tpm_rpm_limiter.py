"""
TPM/RPM 限流器模块

提供了基于 Token Per Minute (TPM) 和 Requests Per Minute (RPM) 的限流器实现。
"""

from aiolimiter import AsyncLimiter

from ai.components.graphrag.llm.limiting.llm_limiter import LLMLimiter


class TpmRpmLLMLimiter(LLMLimiter):
    """
    TPM/RPM 限流器

    同时支持 TPM(每分钟 token 数)和 RPM(每分钟请求数)两种限流方式。
    可以单独使用其中一种,也可以同时使用两种限流。
    """

    _tpm_limiter: AsyncLimiter | None
    _rpm_limiter: AsyncLimiter | None

    def __init__(
        self, tpm_limiter: AsyncLimiter | None, rpm_limiter: AsyncLimiter | None
    ):
        """
        初始化 TPM/RPM 限流器

        Args:
            tpm_limiter: TPM 限流器,如果为 None 则不限制 token 速率
            rpm_limiter: RPM 限流器,如果为 None 则不限制请求速率
        """
        self._tpm_limiter = tpm_limiter
        self._rpm_limiter = rpm_limiter

    @property
    def needs_token_count(self) -> bool:
        """
        是否需要传入 token 数量

        Returns
        -------
            如果配置了 TPM 限流器则返回 True,否则返回 False
        """
        return self._tpm_limiter is not None

    async def acquire(self, num_tokens: int = 1) -> None:
        """
        获取通过限流器的许可

        同时检查 TPM 和 RPM 限制,确保不超过配置的速率。

        Args:
            num_tokens: 本次请求使用的 token 数量
        """
        # 等待 TPM 限流器(如果配置了)
        if self._tpm_limiter is not None:
            await self._tpm_limiter.acquire(num_tokens)
        # 等待 RPM 限流器(如果配置了)
        if self._rpm_limiter is not None:
            await self._rpm_limiter.acquire()
