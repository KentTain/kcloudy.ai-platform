"""基于Rich的CLI进度报告器."""

# 打印迭代进度
import asyncio

from datashaper import Progress as DSProgress
from rich.console import Console, Group
from rich.live import Live
from rich.progress import Progress, TaskID, TimeElapsedColumn
from rich.spinner import Spinner
from rich.tree import Tree

from ai.components.graphrag.index.progress.types import ProgressReporter


# https://stackoverflow.com/a/34325723
class RichProgressReporter(ProgressReporter):
    """基于Rich的CLI进度报告器."""

    _console: Console
    _group: Group
    _tree: Tree
    _live: Live
    _task: TaskID | None = None
    _prefix: str
    _transient: bool
    _disposing: bool = False
    _progressbar: Progress
    _last_refresh: float = 0

    def dispose(self) -> None:
        """释放进度报告器."""
        self._disposing = True
        self._live.stop()

    @property
    def console(self) -> Console:
        """获取控制台."""
        return self._console

    @property
    def group(self) -> Group:
        """获取分组."""
        return self._group

    @property
    def tree(self) -> Tree:
        """获取树."""
        return self._tree

    @property
    def live(self) -> Live:
        """获取实时显示."""
        return self._live

    def __init__(
        self,
        prefix: str,
        parent: "RichProgressReporter | None" = None,
        transient: bool = True,
    ) -> None:
        """创建一个新的基于Rich的进度报告器."""
        self._prefix = prefix

        if parent is None:
            console = Console()
            group = Group(Spinner("dots", prefix), fit=True)
            tree = Tree(group)
            live = Live(
                tree, console=console, refresh_per_second=1, vertical_overflow="crop"
            )
            live.start()

            self._console = console
            self._group = group
            self._tree = tree
            self._live = live
            self._transient = False
        else:
            self._console = parent.console
            self._group = parent.group
            progress_columns = [*Progress.get_default_columns(), TimeElapsedColumn()]
            self._progressbar = Progress(
                *progress_columns, console=self._console, transient=transient
            )

            tree = Tree(prefix)
            tree.add(self._progressbar)
            tree.hide_root = True

            if parent is not None:
                parent_tree = parent.tree
                parent_tree.hide_root = False
                parent_tree.add(tree)

            self._tree = tree
            self._live = parent.live
            self._transient = transient

        self.refresh()

    def refresh(self) -> None:
        """执行防抖刷新."""
        now = asyncio.get_event_loop().time()
        duration = now - self._last_refresh
        if duration > 0.1:
            self._last_refresh = now
            self.force_refresh()

    def force_refresh(self) -> None:
        """强制刷新."""
        self.live.refresh()

    def stop(self) -> None:
        """停止进度报告器."""
        self._live.stop()

    def child(self, prefix: str, transient: bool = True) -> ProgressReporter:
        """创建子进度条."""
        return RichProgressReporter(parent=self, prefix=prefix, transient=transient)

    def error(self, message: str) -> None:
        """报告错误."""
        self._console.print(f"[red]{message}[/red]")

    def warning(self, message: str) -> None:
        """报告警告."""
        self._console.print(f"[yellow]{message}[/yellow]")

    def success(self, message: str) -> None:
        """报告成功."""
        self._console.print(f"[green]{message}[/green]")

    def info(self, message: str) -> None:
        """报告信息."""
        self._console.print(message)

    def __call__(self, progress_update: DSProgress) -> None:
        """更新进度."""
        if self._disposing:
            return
        progressbar = self._progressbar

        if self._task is None:
            self._task = progressbar.add_task(self._prefix)

        progress_description = ""
        if progress_update.description is not None:
            progress_description = f" - {progress_update.description}"

        completed = progress_update.completed_items or progress_update.percent
        total = progress_update.total_items or 1
        progressbar.update(
            self._task,
            completed=completed,
            total=total,
            description=f"{self._prefix}{progress_description}",
        )
        if completed == total and self._transient:
            progressbar.update(self._task, visible=False)

        self.refresh()
