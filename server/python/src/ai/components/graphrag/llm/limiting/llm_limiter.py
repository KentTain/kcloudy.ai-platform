"""
限流器类型定义

定义了 LLM 限流器的基础接口。
"""

from abc import ABC, abstractmethod


class LLMLimiter(ABC):
    """
    LLM 限流器接口

    所有限流器实现都应该继承此抽象类。
    """

    @property
    @abstractmethod
    def needs_token_count(self) -> bool:
        """
        是否需要传入 token 数量

        Returns
        -------
            如果限流器需要知道 token 数量则返回 True,否则返回 False
        """

    @abstractmethod
    async def acquire(self, num_tokens: int = 1) -> None:
        """
        获取通过限流器的许可

        此方法会阻塞直到获得许可为止。

        Args:
            num_tokens: 要获取的 token 数量,默认为 1
        """
