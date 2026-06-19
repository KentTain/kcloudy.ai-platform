"""
LLM 配置协议定义

定义了 LLM 配置对象必须实现的属性。
"""

from typing import Protocol


class LLMConfig(Protocol):
    """
    LLM 配置协议

    定义了 LLM 配置对象必须提供的配置属性。
    """

    @property
    def max_retries(self) -> int | None:
        """
        获取最大重试次数

        Returns
        -------
            最大重试次数,如果未配置则返回 None
        """
        ...

    @property
    def max_retry_wait(self) -> float | None:
        """
        获取最大重试等待时间

        Returns
        -------
            最大重试等待时间(秒),如果未配置则返回 None
        """
        ...

    @property
    def sleep_on_rate_limit_recommendation(self) -> bool | None:
        """
        获取是否遵循速率限制建议

        Returns
        -------
            如果应遵循速率限制建议的睡眠时间则返回 True,如果未配置则返回 None
        """
        ...

    @property
    def tokens_per_minute(self) -> int | None:
        """
        获取每分钟 token 数限制

        Returns
        -------
            每分钟允许的 token 数,如果未配置则返回 None
        """
        ...

    @property
    def requests_per_minute(self) -> int | None:
        """
        获取每分钟请求数限制

        Returns
        -------
            每分钟允许的请求数,如果未配置则返回 None
        """
        ...
