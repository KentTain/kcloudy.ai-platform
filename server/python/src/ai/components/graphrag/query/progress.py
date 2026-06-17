"""编排状态报告器。

Status Reporter for orchestration.
"""

from abc import ABCMeta, abstractmethod
from typing import Any


class StatusReporter(metaclass=ABCMeta):
    """
    提供从管道报告状态更新的方式。

    Provides a way to report status updates from the pipeline.
    """

    @abstractmethod
    def error(self, message: str, details: dict[str, Any] | None = None):
        """
        报告错误。

        Report an error.

        参数 Parameters
        ----------
        - message (str): 错误消息。Error message
        - details (dict[str, Any] | None): 错误详情。Error details
        """

    @abstractmethod
    def warning(self, message: str, details: dict[str, Any] | None = None):
        """
        报告警告。

        Report a warning.

        参数 Parameters
        ----------
        - message (str): 警告消息。Warning message
        - details (dict[str, Any] | None): 警告详情。Warning details
        """

    @abstractmethod
    def log(self, message: str, details: dict[str, Any] | None = None):
        """
        报告日志。

        Report a log.

        参数 Parameters
        ----------
        - message (str): 日志消息。Log message
        - details (dict[str, Any] | None): 日志详情。Log details
        """


class ConsoleStatusReporter(StatusReporter):
    """
    写入控制台的报告器。

    A reporter that writes to a console.
    """

    def error(self, message: str, details: dict[str, Any] | None = None):
        """
        报告错误。

        Report an error.

        参数 Parameters
        ----------
        - message (str): 错误消息。Error message
        - details (dict[str, Any] | None): 错误详情。Error details
        """
        print(message, details)

    def warning(self, message: str, details: dict[str, Any] | None = None):
        """
        报告警告。

        Report a warning.

        参数 Parameters
        ----------
        - message (str): 警告消息。Warning message
        - details (dict[str, Any] | None): 警告详情。Warning details
        """
        _print_warning(message)

    def log(self, message: str, details: dict[str, Any] | None = None):
        """
        报告日志。

        Report a log.

        参数 Parameters
        ----------
        - message (str): 日志消息。Log message
        - details (dict[str, Any] | None): 日志详情。Log details
        """
        print(message, details)


def _print_warning(skk):
    """
    以黄色打印警告消息。

    Print warning message in yellow color.

    参数 Parameters
    ----------
    - skk: 警告消息。Warning message
    """
    print(f"\033[93m {skk}\033[00m")
