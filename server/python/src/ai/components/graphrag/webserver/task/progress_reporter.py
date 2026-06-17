"""基于 Rich 的进度报告器。

Rich-based progress reporter.

此模块提供与任务对象集成的进度报告功能,支持错误,警告,成功和信息消息的格式化输出。
This module provides progress reporting functionality integrated with task objects, supporting formatted output for error, warning, success, and info messages.
"""

# 打印迭代进度 / Print iterations progress

from ai.components.graphrag.index.progress import ProgressReporter
from ai.components.graphrag.index.progress.rich import RichProgressReporter
from ai.components.graphrag.webserver.task.task import Task


class TaskProgressReporter(RichProgressReporter):
    """
    任务进度报告器。

    Task progress reporter.

    基于 Rich 的进度报告器,集成了任务对象的日志记录和进度更新功能。
    Rich-based progress reporter integrated with task object for logging and progress updates.
    """

    def __init__(
        self,
        prefix: str,
        parent: "RichProgressReporter | None" = None,
        transient: bool = True,
        task: Task | None = None,
    ) -> None:
        """
        初始化任务进度报告器。

        Initialize task progress reporter.

        参数 Parameters
        ----------
        prefix : str
            消息前缀。Message prefix.
        parent : RichProgressReporter | None, optional
            父报告器。Parent reporter.
        transient : bool, optional
            是否为临时显示。Whether to display transiently.
        task : Task | None, optional
            关联的任务对象。Associated task object.
        """
        super().__init__(prefix, parent, transient)
        self._task: Task = task
        self.prefix = prefix

    def child(self, prefix: str, transient: bool = True) -> ProgressReporter:
        """
        创建子进度报告器。

        Create a child progress reporter.

        参数 Parameters
        ----------
        prefix : str
            子报告器的消息前缀。Message prefix for child reporter.
        transient : bool, optional
            是否为临时显示。Whether to display transiently.

        返回 Returns
        -------
        ProgressReporter
            子进度报告器实例。Child progress reporter instance.
        """
        return TaskProgressReporter(parent=self, prefix=prefix, transient=transient)

    def error(self, message: str) -> None:
        """
        报告错误。

        Report an error.

        参数 Parameters
        ----------
        message : str
            错误消息。Error message.
        """
        self._console.print(f"[red]{message}[/red]")
        self._task.add_log(f"{self.prefix}ERROR: {message}")

    def warning(self, message: str) -> None:
        """
        报告警告。

        Report a warning.

        参数 Parameters
        ----------
        message : str
            ��告消息。Warning message.
        """
        self._console.print(f"[yellow]{message}[/yellow]")
        self._task.add_log(f"{self.prefix}WARNING: {message}")

    def success(self, message: str) -> None:
        """
        报告成功。

        Report success.

        参数 Parameters
        ----------
        message : str
            成功消息。Success message.
        """
        self._console.print(f"[green]{message}[/green]")
        self._task.add_log(f"{self.prefix}SUCCESS: {message}")
        self._task.add_progress(5)

    def info(self, message: str) -> None:
        """
        报告信息。

        Report information.

        参数 Parameters
        ----------
        message : str
            信息消息。Information message.
        """
        self._console.print(message)
        self._task.add_log(f"{self.prefix}INFO: {message}")
