"""向文件写入的报告器."""

import json
import logging
from io import TextIOWrapper
from pathlib import Path

from datashaper import NoopWorkflowCallbacks

log = logging.getLogger(__name__)


class FileWorkflowCallbacks(NoopWorkflowCallbacks):
    """向文件写入的报告器."""

    _out_stream: TextIOWrapper

    def __init__(self, directory: str):
        """创建基于文件的工作流报告器."""
        Path(directory).mkdir(parents=True, exist_ok=True)
        self._out_stream = open(  # noqa: SIM115
            Path(directory) / "logs.json", "a", encoding="utf-8", errors="strict"
        )

    def on_error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ):
        """处理错误发生时的操作."""
        self._out_stream.write(
            json.dumps(
                {
                    "type": "error",
                    "data": message,
                    "stack": stack,
                    "source": str(cause),
                    "details": details,
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        message = f"{message} details={details}"
        log.info(message)

    def on_warning(self, message: str, details: dict | None = None):
        """处理警告发生时的操作."""
        self._out_stream.write(
            json.dumps(
                {"type": "warning", "data": message, "details": details},
                ensure_ascii=False,
            )
            + "\n"
        )
        _print_warning(message)

    def on_log(self, message: str, details: dict | None = None):
        """处理日志消息产生时的操作."""
        self._out_stream.write(
            json.dumps(
                {"type": "log", "data": message, "details": details}, ensure_ascii=False
            )
            + "\n"
        )

        message = f"{message} details={details}"
        log.info(message)


def _print_warning(skk):
    """
    处理print_warning。

    Args:
        skk: skk 参数。
    """
    log.warning(skk)
