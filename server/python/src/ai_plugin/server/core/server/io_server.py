import contextlib
import logging
import os
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

from ai_plugin.sdk.errors.model import InvokeError
from ai_plugin.server.config.config import AlonPluginEnv
from ai_plugin.server.core.entities.plugin.io import (
    PluginInStream,
    PluginInStreamEvent,
)
from ai_plugin.server.core.server.__base.request_reader import RequestReader
from ai_plugin.server.core.server.__base.response_writer import ResponseWriter
from ai_plugin.server.core.server.stdio.request_reader import StdioRequestReader
from ai_plugin.server.core.server.tcp.request_reader import TCPReaderWriter

logger = logging.getLogger(__name__)


class IOServer(ABC):
    """
    IO服务器基类

    提供插件服务器的基础输入输出处理功能，包括请求监听、任务执行和响应处理
    """

    # 请求读取器
    request_reader: RequestReader

    def __init__(
        self,
        config: AlonPluginEnv,
        request_reader: RequestReader,
        default_writer: ResponseWriter | None,
    ) -> None:
        """
        初始化IO服务器

        Args:
            config: 插件环境配置
            request_reader: 请求读取器
            default_writer: 默认响应写入器，可选
        """
        self.config = config
        self.default_writer = default_writer
        self.executer = ThreadPoolExecutor(max_workers=self.config.MAX_WORKER)
        self.request_reader = request_reader

    def close(self, *args):
        """
        关闭服务器

        Args:
            *args: 可变参数
        """
        self.request_reader.close()

    @abstractmethod
    def _execute_request(
        self,
        session_id: str,
        data: dict,
        reader: RequestReader,
        writer: ResponseWriter,
        conversation_id: str | None = None,
        message_id: str | None = None,
        app_id: str | None = None,
        endpoint_id: str | None = None,
    ):
        """
        执行请求（抽象方法）

        接收请求并执行它们，应该在子类中实现

        Args:
            session_id: 会话ID
            data: 请求数据
            reader: 请求读取器
            writer: 响应写入器
            conversation_id: 对话ID，可选
            message_id: 消息ID，可选
            app_id: 应用ID，可选
            endpoint_id: 端点ID，可选
        """

    def _setup_instruction_listener(self):
        """
        设置指令监听器

        开始监听标准输入并将任务分派给执行器
        """

        def filter(data: PluginInStream) -> bool:
            return data.event == PluginInStreamEvent.Request

        for data in self.request_reader.read(filter).read():
            self.executer.submit(
                self._execute_request_in_thread,
                data.session_id,
                data.data,
                data.reader,
                data.writer,
                data.conversation_id,
                data.message_id,
                data.app_id,
                data.endpoint_id,
            )

    def _execute_request_in_thread(
        self,
        session_id: str,
        data: dict,
        reader: RequestReader,
        writer: ResponseWriter,
        conversation_id: str | None = None,
        message_id: str | None = None,
        app_id: str | None = None,
        endpoint_id: str | None = None,
    ):
        """
        在线程中执行请求

        _execute_request的包装器，处理异常和响应

        Args:
            session_id: 会话ID
            data: 请求数据
            reader: 请求读取器
            writer: 响应写入器
            conversation_id: 对话ID，可选
            message_id: 消息ID，可选
            app_id: 应用ID，可选
            endpoint_id: 端点ID，可选
        """
        # 等待任务完成
        try:
            self._execute_request(
                session_id,
                data,
                reader,
                writer,
                conversation_id,
                message_id,
                app_id,
                endpoint_id,
            )
        except Exception as e:
            args = {}
            if isinstance(e, InvokeError):
                args["description"] = e.description

            if isinstance(reader, (TCPReaderWriter)):
                logger.exception(
                    "执行请求时发生意外错误",
                    exc_info=e,
                )

            writer.session_message(
                session_id=session_id,
                data=writer.stream_error_object(
                    data={
                        "error_type": type(e).__name__,
                        "message": str(e),
                        "args": args,
                    },
                ),
            )

        writer.session_message(session_id=session_id, data=writer.stream_end_object())
        writer.done()

    def _heartbeat(self):
        """
        发送心跳包

        向标准输出发送心跳包以保持连接活跃
        """
        assert self.default_writer

        while True:
            # 定时器
            with contextlib.suppress(Exception):
                self.default_writer.heartbeat()
            time.sleep(self.config.HEARTBEAT_INTERVAL)

    def _parent_alive_check(self):
        """
        检查父进程是否存活

        监控父进程状态，如果父进程终止则退出当前进程
        """
        while True:
            time.sleep(0.5)
            parent_process_id = os.getppid()
            if parent_process_id == 1:
                os._exit(-1)

    def _run(self):
        th1 = Thread(target=self._setup_instruction_listener)
        th2 = Thread(target=self.request_reader.event_loop)
        th3 = None

        if self.default_writer:
            th3 = Thread(target=self._heartbeat)

        if isinstance(self.request_reader, StdioRequestReader):
            Thread(target=self._parent_alive_check).start()

        th1.start()
        th2.start()

        if th3 is not None:
            th3.start()

        th1.join()
        th2.join()

        if th3 is not None:
            th3.join()

    def run(self):
        """
        启动插件服务器

        开始运行插件服务器，包括监听线程、事件循环和心跳检测
        """
        self._run()
