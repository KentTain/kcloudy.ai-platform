"""状态报告类型."""

from abc import ABC, abstractmethod

from datashaper import Progress


class ProgressReporter(ABC):
    """
    进度报告器的抽象基类。

    用于通过进度条等机制报告工作流处理进度。
    """

    @abstractmethod
    def __call__(self, update: Progress):
        """更新进度."""

    @abstractmethod
    def dispose(self):
        """释放进度报告器."""

    @abstractmethod
    def child(self, prefix: str, transient=True) -> "ProgressReporter":
        """创建子进度条."""

    @abstractmethod
    def force_refresh(self) -> None:
        """强制刷新."""

    @abstractmethod
    def stop(self) -> None:
        """停止进度报告器."""

    @abstractmethod
    def error(self, message: str) -> None:
        """报告错误."""

    @abstractmethod
    def warning(self, message: str) -> None:
        """报告警告."""

    @abstractmethod
    def info(self, message: str) -> None:
        """报告信息."""

    @abstractmethod
    def success(self, message: str) -> None:
        """报告成功."""


class NullProgressReporter(ProgressReporter):
    """不执行任何操作的进度报告器."""

    def __call__(self, update: Progress) -> None:
        """更新进度."""

    def dispose(self) -> None:
        """释放进度报告器."""

    def child(self, prefix: str, transient: bool = True) -> ProgressReporter:
        """创建子进度条."""
        return self

    def force_refresh(self) -> None:
        """强制刷新."""

    def stop(self) -> None:
        """停止进度报告器."""

    def error(self, message: str) -> None:
        """报告错误."""

    def warning(self, message: str) -> None:
        """报告警告."""

    def info(self, message: str) -> None:
        """报告信息."""

    def success(self, message: str) -> None:
        """报告成功."""


class PrintProgressReporter(ProgressReporter):
    """打印进度报告器."""

    prefix: str

    def __init__(self, prefix: str):
        """创建新的进度报告器."""
        self.prefix = prefix
        print(f"\n{self.prefix}", end="")

    def __call__(self, update: Progress) -> None:
        """更新进度."""
        print(".", end="")

    def dispose(self) -> None:
        """释放进度报告器."""

    def child(self, prefix: str, transient: bool = True) -> "ProgressReporter":
        """创建子进度条."""
        return PrintProgressReporter(prefix)

    def stop(self) -> None:
        """停止进度报告器."""

    def force_refresh(self) -> None:
        """强制刷新."""

    def error(self, message: str) -> None:
        """报告错误."""
        print(f"\n{self.prefix}ERROR: {message}")

    def warning(self, message: str) -> None:
        """报告警告."""
        print(f"\n{self.prefix}WARNING: {message}")

    def info(self, message: str) -> None:
        """报告信息."""
        print(f"\n{self.prefix}INFO: {message}")

    def success(self, message: str) -> None:
        """报告成功."""
        print(f"\n{self.prefix}SUCCESS: {message}")
