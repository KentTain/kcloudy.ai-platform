"""
OpenAI DataShaper 包的错误定义

定义了 LLM 调用过程中可能出现的自定义异常。
"""


class RetriesExhaustedError(RuntimeError):
    """
    重试次数耗尽错误

    当 LLM 操作经过多次重试后仍然失败时抛出此异常。
    """

    def __init__(self, name: str, num_retries: int) -> None:
        """
        初始化重试耗尽错误

        Args:
            name: 操作名称
            num_retries: 已执行的重试次数
        """
        super().__init__(f"Operation '{name}' failed - {num_retries} retries exhausted")
