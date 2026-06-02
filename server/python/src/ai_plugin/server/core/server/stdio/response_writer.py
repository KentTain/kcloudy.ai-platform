import sys

from ai_plugin.server.core.server.__base.response_writer import ResponseWriter


class StdioResponseWriter(ResponseWriter):
    """标准输出响应写入器，将数据写入标准输出流"""

    def write(self, data: str):
        """
        将数据写入标准输出

        Args:
            data: 要写入的字符串数据
        """
        sys.stdout.write(data)
        sys.stdout.flush()  # 确保数据立即输出

    def done(self):
        """
        完成当前轮次的处理

        对于标准输出写入器，无需特殊处理
        """
        pass
