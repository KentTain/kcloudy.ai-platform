"""
组合限流器模块

提供了可以组合多个限流器的实现。
"""

from ai.components.graphrag.llm.limiting.llm_limiter import LLMLimiter


class CompositeLLMLimiter(LLMLimiter):
    """
    组合限流器

    允许多个限流器同时工作,所有限流器都必须允许才能通过。
    常用于同时应用多种不同的限流策略。
    """

    _limiters: list[LLMLimiter]

    def __init__(self, limiters: list[LLMLimiter]):
        """
        初始化组合限流器

        Args:
            limiters: 限流器列表,所有限流器都会被依次检查
        """
        self._limiters = limiters

    @property
    def needs_token_count(self) -> bool:
        """
        是否需要传入 token 数量

        Returns
        -------
            如果任一限流器需要 token 数量则返回 True,否则返回 False
        """
        return any(limiter.needs_token_count for limiter in self._limiters)

    async def acquire(self, num_tokens: int = 1) -> None:
        """
        获取通过所有限流器的许可

        依次检查每个限流器,所有限流器都必须允许才能通过。

        Args:
            num_tokens: 本次请求使用的 token 数量
        """
        for limiter in self._limiters:
            await limiter.acquire(num_tokens)
