import errno
import logging
import os
import signal
import socket as native_socket
import time
from collections.abc import Callable, Generator
from threading import Lock
from typing import Any

from gevent import sleep
from gevent import socket as gevent_socket
from gevent.select import select
from pydantic import TypeAdapter

from ai_plugin.server.core.entities.message import InitializeMessage
from ai_plugin.server.core.entities.plugin.io import (
    PluginInStream,
    PluginInStreamEvent,
)
from ai_plugin.server.core.server.__base.request_reader import RequestReader
from ai_plugin.server.core.server.__base.response_writer import ResponseWriter


logger = logging.getLogger(__name__)


class TCPReaderWriter(RequestReader, ResponseWriter):
    """TCP读取器写入器类，同时实现TCP连接的读取和写入功能"""

    def __init__(
        self,
        host: str,
        port: int,
        key: str,
        reconnect_attempts: int = 3,
        reconnect_timeout: int = 5,
        on_connected: Callable | None = None,
    ):
        """
        初始化TCPStream并连接到目标，如果连接失败则抛出异常

        Args:
            host: 目标主机地址
            port: 目标端口号
            key: 认证密钥
            reconnect_attempts: 重连尝试次数，默认3次
            reconnect_timeout: 重连超时时间（秒），默认5秒
            on_connected: 可选的连接成功回调函数
        """
        super().__init__()

        self.host = host
        self.port = port
        self.key = key
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_timeout = reconnect_timeout
        self.alive = False  # 连接状态标识
        self.on_connected = on_connected
        self.opt_lock = Lock()  # 操作锁，用于线程安全

        # 处理SIGINT信号以平滑退出程序（由于gevent的限制）
        signal.signal(signal.SIGINT, lambda *args, **kwargs: os._exit(0))

    def launch(self):
        """
        启动连接
        """
        self._launch()

    def close(self):
        """
        关闭连接

        如果连接处于活动状态，则关闭socket并更新状态
        """
        if self.alive:
            self.sock.close()
            self.alive = False

    def _write_to_sock(self, data: bytes):
        """
        向socket写入数据

        Args:
            data: 要写入的字节数据

        Returns:
            int: 实际写入的字节数

        使用锁确保写入操作的线程安全
        """
        with self.opt_lock:
            return self.sock.send(data)

    def _recv_from_sock(self, size: int) -> bytes:
        """
        从socket接收数据

        Args:
            size: 要接收的数据大小

        Returns:
            bytes: 接收到的字节数据
        """
        return self.sock.recv(size)

    def write(self, data: str):
        """
        写入字符串数据到socket

        Args:
            data: 要写入的字符串数据

        Raises:
            Exception: 当连接已断开时抛出异常

        根据socket类型采用不同的写入策略：
        - gevent socket：非阻塞，逐字节发送避免BlockingIOError
        - 原生socket：使用sendall一次性发送所有数据
        """
        if not self.alive:
            raise Exception("连接已断开")

        try:
            if native_socket.socket is gevent_socket.socket:
                """
                gevent socket是非阻塞的，为了避免BlockingIOError
                需要逐字节发送数据
                """
                data_bytes = data.encode()
                while data_bytes:
                    try:
                        sent = self._write_to_sock(data_bytes)
                        data_bytes = data_bytes[sent:]
                    except BlockingIOError as e:
                        if e.errno != errno.EAGAIN:
                            raise
                        sleep(0)
            else:
                self.sock.sendall(data.encode())
        except Exception:
            logger.exception("写入数据失败")
            self._launch()

    def done(self):
        """
        完成当前轮次的处理

        对于TCP连接，无需特殊处理
        """
        pass

    def _launch(self):
        """
        连接到目标，如果失败则尝试重连

        根据重连配置进行多次连接尝试，每次失败后等待指定时间
        """
        attempts = 0
        while attempts < self.reconnect_attempts:
            try:
                self._connect()
                break
            except Exception as e:
                attempts += 1
                if attempts >= self.reconnect_attempts:
                    raise e

                time.sleep(self.reconnect_timeout)

    def _connect(self):
        """
        建立TCP连接

        根据socket类型创建连接，发送握手消息完成认证

        Raises:
            OSError: 连接失败时抛出异常
        """
        try:
            # 根据socket类型创建连接
            if native_socket.socket is gevent_socket.socket:
                self.sock = gevent_socket.create_connection((self.host, self.port))
            else:
                self.sock = native_socket.create_connection((self.host, self.port))

            self.alive = True

            # 发送握手消息
            handshake_message = InitializeMessage(
                type=InitializeMessage.Type.HANDSHAKE,
                data=InitializeMessage.Key(key=self.key).model_dump(),
            )
            self.sock.sendall(handshake_message.model_dump_json().encode() + b"\n")

            logger.info(f"\033[32m已连接到 {self.host}:{self.port}\033[0m")

            # 执行连接成功回调
            if self.on_connected:
                self.on_connected()

            logger.info(f"已向 {self.host}:{self.port} 发送密钥")
        except OSError as e:
            logger.exception(f"\033[31m连接到 {self.host}:{self.port} 失败\033[0m")
            raise e

    def _read_stream(self) -> Generator[PluginInStream, None, None]:
        """
        从目标读取数据流

        Yields:
            PluginInStream: 解析后的插件输入流对象

        持续监听socket连接，接收并解析数据，生成PluginInStream对象
        处理连接异常并自动重连
        """
        buffer = b""  # 数据缓冲区
        while self.alive:
            try:
                # 使用select检查socket是否有数据可读
                ready_to_read, _, _ = select([self.sock], [], [], 1)
                if not ready_to_read:
                    continue

                try:
                    # 接收数据（最大1MB）
                    data = self._recv_from_sock(1048576)
                except BlockingIOError as e:
                    if native_socket.socket is gevent_socket.socket:
                        if e.errno != errno.EAGAIN:
                            raise
                        sleep(0)
                        continue
                    else:
                        raise

                if data == b"":
                    raise Exception("连接已关闭")

            except Exception:
                logger.exception(
                    f"\033[31m从 {self.host}:{self.port} 读取数据失败\033[0m"
                )
                self.alive = False
                time.sleep(self.reconnect_timeout)
                self._launch()
                continue

            if not data:
                continue

            buffer += data

            # 按行处理数据，保留最后一行（如果不完整）
            lines = buffer.split(b"\n")
            if len(lines) == 0:
                continue

            buffer = lines[-1]  # 保留最后一行（可能不完整）

            # 处理除最后一行外的所有行
            lines = lines[:-1]
            for line in lines:
                try:
                    # 解析JSON数据
                    data = TypeAdapter(dict[str, Any]).validate_json(line)
                    chunk = PluginInStream(
                        session_id=data["session_id"],
                        conversation_id=data.get("conversation_id"),
                        message_id=data.get("message_id"),
                        app_id=data.get("app_id"),
                        endpoint_id=data.get("endpoint_id"),
                        event=PluginInStreamEvent.value_of(data["event"]),
                        data=data["data"],
                        reader=self,
                        writer=self,
                    )
                    yield chunk
                    logger.info(
                        f"接收到事件: \n{chunk.event}\n 会话ID: \n{chunk.session_id}\n 数据: \n{chunk.data}"
                    )
                except Exception:
                    logger.exception(f"\033[31m解析数据时发生错误: {line}\033[0m")
