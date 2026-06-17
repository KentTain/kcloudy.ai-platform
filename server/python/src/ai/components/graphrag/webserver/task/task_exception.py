"""提供组件图谱检索增强生成相关功能。"""


class TaskStopError(RuntimeError):
    """
    任务停止异常。

    Task stop exception.

    当任务需要被强制停止时抛出此异常。
    Raised when a task needs to be forcefully stopped.
    """

    def __init__(self, msg: str) -> None:
        """
        初始化任务停止异常。

        Initialize task stop exception.

        参数 Parameters
        ----------
        msg : str
            错误消息。Error message.
        """
        super().__init__(f"stop msg: {msg}")
