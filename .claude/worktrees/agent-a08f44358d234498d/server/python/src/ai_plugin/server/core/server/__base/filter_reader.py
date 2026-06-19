import queue
from collections.abc import Callable, Generator
from queue import Queue
from typing import overload

from ai_plugin.server.core.entities.plugin.io import PluginInStream


class FilterReader:
    """过滤读取器类，用于根据过滤条件读取和处理数据流"""

    filter: Callable[[PluginInStream], bool]  # 过滤函数
    queue: Queue[PluginInStream | None]  # 数据队列
    close_callback: Callable | None  # 关闭回调函数

    def __init__(
        self,
        filter: Callable[[PluginInStream], bool],
        close_callback: Callable | None = None,
    ) -> None:
        """
        初始化过滤读取器

        Args:
            filter: 过滤函数，用于判断是否处理特定的PluginInStream数据
            close_callback: 可选的关闭回调函数，在读取器关闭时调用
        """
        self.filter = filter
        self.queue = Queue()  # 创建线程安全的队列
        self.close_callback = close_callback

    @overload
    def read(
        self, timeout_for_round: float
    ) -> Generator[PluginInStream | None, None, None]: ...

    @overload
    def read(self) -> Generator[PluginInStream, None, None]: ...

    def read(
        self, timeout_for_round: float | None = None
    ) -> Generator[PluginInStream | None, None, None]:
        """
        从队列中读取数据

        Args:
            timeout_for_round: 可选的超时时间（秒），如果指定则允许返回None

        Yields:
            PluginInStream | None: 队列中的数据项，如果设置了超时且超时则返回None

        当队列中接收到None时停止读取，这表示流已结束
        """
        while True:
            try:
                # 从队列获取数据，可以设置超时
                data = self.queue.get(timeout=timeout_for_round)
                if data is None:
                    # None是结束信号
                    break

                yield data
            except queue.Empty:
                # 队列为空且已超时，返回None（仅在设置了超时时）
                yield None
            except Exception:
                # 发生异常时停止读取
                break

    def close(self):
        """
        关闭过滤读取器

        调用关闭回调函数（如果存在）并向队列发送结束信号
        """
        if self.close_callback:
            self.close_callback()

        # 向队列发送None作为结束信号
        self.queue.put(None)

    def write(self, data: PluginInStream):
        """
        向队列写入数据

        Args:
            data: 要写入的PluginInStream数据
        """
        self.queue.put(data)

    def __enter__(self):
        """
        上下文管理器入口

        Returns:
            FilterReader: 返回自身实例
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        上下文管理器出口

        Args:
            exc_type: 异常类型
            exc_value: 异常值
            traceback: 异常追踪信息

        自动关闭读取器
        """
        self.close()
