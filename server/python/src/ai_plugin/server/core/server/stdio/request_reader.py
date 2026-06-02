import sys
from collections.abc import Generator
from typing import Any

from gevent.os import tp_read
from pydantic import TypeAdapter

from ai_plugin.server.core.entities.plugin.io import (
    PluginInStream,
    PluginInStreamEvent,
)
from ai_plugin.server.core.server.__base.request_reader import RequestReader
from ai_plugin.server.core.server.stdio.response_writer import StdioResponseWriter


class StdioRequestReader(RequestReader):
    """标准输入请求读取器，从标准输入流读取数据"""

    def __init__(self):
        """初始化标准输入请求读取器"""
        super().__init__()

    def _read_async(self) -> bytes:
        """
        异步读取标准输入数据

        使用tp_read以64KB块的形式从标准输入读取数据
        标准输入的操作系统缓冲区通常是64KB，因此使用更大的值没有意义

        Returns:
            bytes: 读取到的字节数据
        """
        return tp_read(sys.stdin.fileno(), 65536)

    def _read_stream(self) -> Generator[PluginInStream, None, None]:
        """
        从标准输入流读取数据流

        Yields:
            PluginInStream: 解析后的插件输入流对象

        持续读取标准输入，按行解析JSON数据并生成PluginInStream对象
        """
        buffer = b""  # 数据缓冲区
        while True:
            # 异步读取数据
            data = self._read_async()
            if not data:
                continue

            buffer += data

            # 如果数据中没有换行符，跳到下一次迭代
            if data.find(b"\n") == -1:
                continue

            # 按行处理数据，保留最后一行（如果不完整）
            lines = buffer.split(b"\n")
            buffer = lines[-1]  # 保留最后一行（可能不完整）

            # 处理除最后一行外的所有行
            lines = lines[:-1]
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                try:
                    # 解析JSON数据
                    data = TypeAdapter(dict[str, Any]).validate_json(line)
                    yield PluginInStream(
                        session_id=data["session_id"],
                        conversation_id=data.get("conversation_id"),
                        message_id=data.get("message_id"),
                        app_id=data.get("app_id"),
                        endpoint_id=data.get("endpoint_id"),
                        event=PluginInStreamEvent.value_of(data["event"]),
                        data=data["data"],
                        reader=self,
                        writer=StdioResponseWriter(),
                    )
                except Exception as e:
                    # 解析失败时发送错误响应
                    StdioResponseWriter().error(data={"error": str(e)})
