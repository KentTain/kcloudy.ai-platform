"""工作流引擎的控制台报告器."""

from datashaper import NoopWorkflowCallbacks


class ConsoleWorkflowCallbacks(NoopWorkflowCallbacks):
    """向控制台写入的报告器."""

    def on_error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ):
        """处理错误发生时的操作."""
        print(message, str(cause), stack, details)

    def on_warning(self, message: str, details: dict | None = None):
        """处理警告发生时的操作."""
        _print_warning(message)

    def on_log(self, message: str, details: dict | None = None):
        """处理日志消息产生时的操作."""
        print(message, details)


def _print_warning(skk):
    """
    处理print_warning。

    Args:
        skk: skk 参数。
    """
    print(f"\033[93m {skk}\033[00m")
