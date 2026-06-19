import logging
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_plugin.server.core.entities.plugin.io import PluginInStream

from ai_plugin.server.core.server.__base.filter_reader import (
    FilterReader,
)

logger = logging.getLogger(__name__)


class RequestReader(ABC):
    """请求读取器抽象基类"""

    def __init__(self):
        """
        初始化请求读取器

        将类变量转换为实例变量以避免全局锁争用
        """
        self.lock = threading.Lock()  # 线程锁，用于保护读取器列表
        self.readers = []  # 读取器列表

    @abstractmethod
    def _read_stream(self) -> Generator["PluginInStream", None, None]:
        """
        从输入流读取数据的抽象方法

        Returns:
            生成器，产出PluginInStream对象

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError

    def event_loop(self):
        """
        事件循环，逐行读取并处理数据

        持续运行直到程序终止，处理从输入流接收到的所有数据
        """
        # 逐行读取并处理
        while True:
            try:
                for line in self._read_stream():
                    self._process_line(line)
            except Exception:
                logger.exception("事件循环中发生错误")
                time.sleep(0.01)  # 防止高CPU使用率

    def _process_line(self, data: "PluginInStream"):
        """
        处理单行数据

        Args:
            data: 插件输入流数据

        对每个数据行进行处理，包括过滤和分发给相应的读取器
        """
        try:
            session_id = data.session_id
            readers_to_process = []

            # 获取锁以安全访问读取器列表
            self.lock.acquire()
            try:
                # 在锁保护下安全复制读取器列表
                readers_to_process = self.readers.copy()
            finally:
                self.lock.release()

            # 在锁外执行过滤操作
            matched_readers = []
            for reader in readers_to_process:
                try:
                    result = reader.filter(data)
                    if result:
                        matched_readers.append(reader)
                except Exception:
                    logger.exception("过滤器执行错误")

            # 分批处理读取器以避免阻塞
            for reader in matched_readers:
                try:
                    reader.write(data)
                except Exception:
                    logger.exception("写入读取器时发生错误")

        except Exception as e:
            # 如果处理失败，向客户端发送错误响应
            data.writer.error(
                session_id=session_id,
                data={"error": f"处理请求失败 ({type(e).__name__}): {e!s}"},
            )

    def read(self, filter: Callable[["PluginInStream"], bool]) -> FilterReader:
        """
        创建并注册一个过滤读取器

        Args:
            filter: 过滤函数，用于判断是否处理特定数据

        Returns:
            FilterReader: 过滤读取器实例
        """

        def close(reader: FilterReader):
            """
            关闭回调函数，用于从读取器列表中移除指定读取器

            Args:
                reader: 要移除的读取器
            """
            self.lock.acquire()
            try:
                if reader in self.readers:
                    self.readers.remove(reader)
            finally:
                self.lock.release()

        # 创建过滤读取器
        reader = FilterReader(filter, close_callback=lambda: close(reader))

        # 将读取器添加到列表中
        self.lock.acquire()
        try:
            self.readers.append(reader)
        finally:
            self.lock.release()

        return reader

    def close(self):
        """
        关闭输入流处理

        清理所有注册的读取器并释放资源
        """
        readers_to_close = []

        # 在锁保护下复制并清空读取器列表
        self.lock.acquire()
        try:
            readers_to_close = self.readers.copy()
            self.readers.clear()
        finally:
            self.lock.release()

        # 在锁外关闭读取器
        for reader in readers_to_close:
            try:
                reader.close()
            except Exception:
                logger.exception("关闭读取器时发生错误")
