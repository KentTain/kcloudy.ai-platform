"""向 ProgressReporter 发送更新的工作流回调管理器."""

from typing import Any

from datashaper import ExecutionNode, NoopWorkflowCallbacks, Progress, TableContainer

from ai.components.graphrag.index.progress import ProgressReporter


class ProgressWorkflowCallbacks(NoopWorkflowCallbacks):
    """委托给 ProgressReporter 的回调管理器."""

    _root_progress: ProgressReporter
    _progress_stack: list[ProgressReporter]

    def __init__(self, progress: ProgressReporter) -> None:
        """创建新的 ProgressWorkflowCallbacks."""
        self._progress = progress
        self._progress_stack = [progress]

    def _pop(self) -> None:
        """处理pop。"""
        self._progress_stack.pop()

    def _push(self, name: str) -> None:
        """
        处理push。

        Args:
            name (str): name 参数。
        """
        self._progress_stack.append(self._latest.child(name))

    @property
    def _latest(self) -> ProgressReporter:
        """
        处理latest。

        Returns:
            处理结果。
        """
        return self._progress_stack[-1]

    def on_workflow_start(self, name: str, instance: object) -> None:
        """工作流开始时执行此回调."""
        self._push(name)

    def on_workflow_end(self, name: str, instance: object) -> None:
        """工作流结束时执行此回调."""
        self._pop()

    def on_step_start(self, node: ExecutionNode, inputs: dict[str, Any]) -> None:
        """每次步骤开始时执行此回调."""
        verb_id_str = f" ({node.node_id})" if node.has_explicit_id else ""
        self._push(f"Verb {node.verb.name}{verb_id_str}")
        self._latest(Progress(percent=0))

    def on_step_end(self, node: ExecutionNode, result: TableContainer | None) -> None:
        """每次步骤结束时执行此回调."""
        self._pop()

    def on_step_progress(self, node: ExecutionNode, progress: Progress) -> None:
        """处理进度发生时的操作."""
        self._latest(progress)
