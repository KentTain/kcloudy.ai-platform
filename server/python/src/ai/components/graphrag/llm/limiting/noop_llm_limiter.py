"""
空操作限流器模块

提供了一个不做任何限制的限流器实现,用于测试或禁用限流。
"""

from ai.components.graphrag.llm.limiting.llm_limiter import LLMLimiter


class NoopLLMLimiter(LLMLimiter):
    """
    空操作限流器

    此限流器不执行任何实际的限流操作,所有请求都会立即通过。
    主要用于测试或在不需要限流的场景中使用。
    """

    @property
    def needs_token_count(self) -> bool:
        """
        是否需要传入 token 数量

        Returns
        -------
            始终返回 False,因为此限流器不需要 token 数量信息
        """
        return False

    async def acquire(self, num_tokens: int = 1) -> None:
        """
        获取通过限流器的许可

        此方法不做任何操作,立即返回。

        Args:
            num_tokens: token 数量(此参数被忽略)
        """
        # 不做任何操作
