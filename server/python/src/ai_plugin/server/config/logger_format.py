import json
import logging
import sys


class AlonPluginLoggerFormatter(logging.Formatter):
    """
    AlonPlugin日志格式化器

    将日志记录格式化为JSON格式输出
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录

        Args:
            record: 日志记录对象

        Returns:
            str: JSON格式的日志字符串
        """
        return json.dumps(
            {
                "event": "log",
                "data": {
                    "level": record.levelname,  # 日志级别
                    "message": record.getMessage(),  # 日志消息
                    "timestamp": record.created,  # 时间戳
                },
            },
        )


# 创建插件日志处理器
plugin_logger_handler = logging.StreamHandler(sys.stdout)
plugin_logger_handler.setLevel(logging.INFO)
plugin_logger_handler.setFormatter(AlonPluginLoggerFormatter())
