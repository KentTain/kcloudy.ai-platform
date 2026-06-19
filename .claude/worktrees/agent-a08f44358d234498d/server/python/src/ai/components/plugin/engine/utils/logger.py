"""
日志工具模块
提供统一的日志配置和管理功能
"""

import sys
from pathlib import Path

from loguru import logger

from ai.components.plugin.engine.config.settings import plugin_settings
from framework.configs.settings import Settings


def _get_plugin_base_dir() -> Path | None:
    """获取插件基础目录

    TODO: 需要在 framework.configs.settings 中添加 PluginSettings 配置
    """
    settings = Settings()
    plugin_settings_obj = getattr(settings, "plugin", None)
    if plugin_settings_obj is not None:
        return getattr(plugin_settings_obj, "plugin_base_dir", None)
    return None


def setup_logging():
    """设置日志配置"""
    # 移除默认的处理器
    logger.remove()

    # 控制台输出格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 文件输出格式
    file_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"

    # 添加控制台处理器
    logger.add(
        sys.stderr,
        format=console_format,
        level=plugin_settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 添加文件处理器（如果配置了日志文件）
    if plugin_settings.log_file:
        log_file = Path(plugin_settings.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            format=file_format,
            level=plugin_settings.log_level,
            rotation=plugin_settings.log_rotation,
            retention=plugin_settings.log_retention,
            compression="gz",
            backtrace=True,
            diagnose=True,
        )

    # 为插件单独配置日志文件
    plugin_base_dir = _get_plugin_base_dir()
    if plugin_base_dir:
        plugin_log_dir = plugin_base_dir / "logs"
        plugin_log_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            plugin_log_dir / "plugins.log",
            format=file_format,
            level="DEBUG",
            rotation="50 MB",
            retention="7 days",
            compression="gz",
            filter=lambda record: "plugin" in record["extra"],
        )


def get_logger(name: str, plugin_name: str | None = None):
    """获取日志记录器

    Args:
        name: 日志记录器名称
        plugin_name: 插件名称（可选）

    Returns:
        配置好的日志记录器
    """
    if plugin_name:
        return logger.bind(plugin=plugin_name, logger_name=name)
    return logger.bind(logger_name=name)


class PluginLogger:
    """插件专用日志记录器"""

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.logger = get_logger(f"plugin.{plugin_name}", plugin_name)

        # 为插件创建专用日志文件
        plugin_base_dir = _get_plugin_base_dir()
        if plugin_base_dir:
            plugin_log_file = (
                plugin_base_dir / plugin_name / "plugin.log"
            )
            plugin_log_file.parent.mkdir(parents=True, exist_ok=True)

            # 添加插件专用的文件处理器
            logger.add(
                plugin_log_file,
                format=("{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}"),
                level="DEBUG",
                rotation="10 MB",
                retention="7 days",
                filter=lambda record: record["extra"].get("plugin") == plugin_name,
            )

    def debug(self, message: str, **kwargs):
        """调试日志"""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """信息日志"""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """警告日志"""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """错误日志"""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """异常日志"""
        self.logger.exception(message, **kwargs)
