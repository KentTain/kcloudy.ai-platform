"""速率限制器工具."""

import asyncio
import time


class RateLimiter:
    """
    原始的TpmRpmLLMLimiter策略在调度时未考虑基于分钟的速率限制。

    引入RateLimiter是为了确保CommunityReportsExtractor可以按每分钟的速率配置进行调度。
    """

    # TODO: RateLimiter scheduled: 使用asyncio实现async_mode

    def __init__(self, rate: int, per: int):
        """
        初始化实例。

        Args:
            rate (int): rate 参数。
            per (int): per 参数。
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.monotonic()

    async def acquire(self):
        """从速率限制器获取令牌."""
        current = time.monotonic()
        elapsed = current - self.last_check
        self.last_check = current
        self.allowance += elapsed * (self.rate / self.per)

        if self.allowance > self.rate:
            self.allowance = self.rate

        if self.allowance < 1.0:
            sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
            await asyncio.sleep(sleep_time)
            self.allowance = 0.0
        else:
            self.allowance -= 1.0
