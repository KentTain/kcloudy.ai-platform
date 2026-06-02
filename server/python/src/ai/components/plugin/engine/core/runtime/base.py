"""
插件运行时基础类
定义插件运行时的基础接口和生命周期管理
"""

import abc
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru._logger import Logger

from ai.components.plugin.engine.models.plugin import PluginInfo


class PluginRuntimeState:
    """插件运行时状态枚举"""

    UNKNOWN = "unknown"
    PREPARING = "preparing"  # 安装预处理中
    PREPARED = "prepared"  # 预处理完成
    STARTING = "starting"  # 启动中
    RUNNING = "running"  # 运行中
    STOPPING = "stopping"  # 停止中
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误状态


class PluginRuntime(abc.ABC):
    """插件运行时基础类"""

    def __init__(self, plugin_info: PluginInfo, workspace_dir: Path):
        self.plugin_info = plugin_info

        plugin_config = plugin_info.config

        # 存储插件信息
        self.plugin_id = (
            f"{plugin_config.configuration.author}/{plugin_config.configuration.name}"
        )
        self.plugin_author = plugin_config.configuration.author
        self.plugin_name = plugin_config.configuration.name
        self.plugin_version = plugin_config.configuration.version

        # 获取带插件信息的logger
        self._plugin_logger: Logger = self._get_plugin_logger()

        self._plugin_logger.info(f"插件作者: {self.plugin_author}")
        self._plugin_logger.info(f"插件名称: {self.plugin_name}")
        self._plugin_logger.info(f"插件版本: {self.plugin_version}")

        if not plugin_config:
            raise RuntimeError("plugin_config未设置")

        self.plugin_config = plugin_config

        self.plugin_name = plugin_config.configuration.name
        self.plugin_version = plugin_config.configuration.version

        self.workspace_dir: Path = workspace_dir

        # 运行时状态
        self._state = PluginRuntimeState.UNKNOWN
        self._is_prepared = False
        self._is_running = False
        self._is_stopping = False

        # 时间戳
        self.prepared_at: datetime | None = None
        self.started_at: datetime | None = None
        self.stopped_at: datetime | None = None

        # 运行时信息
        self.process_id: int | None = None
        self.port: int | None = None

    @property
    def state(self) -> str:
        """获取当前状态"""
        return self._state

    @property
    def is_prepared(self) -> bool:
        """是否已完成预处理"""
        return self._is_prepared

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running

    @abc.abstractmethod
    async def prepare(self) -> None:
        """
        安装时重量级预处理
        包括：环境准备、依赖安装、文件预编译、安全扫描等
        这个方法是幂等的，可以重复执行
        """
        pass

    @abc.abstractmethod
    async def start(self) -> None:
        """
        轻量级快速启动
        前提：已经完成prepare()
        包括：启动进程、端口分配、健康检查等
        """
        pass

    @abc.abstractmethod
    async def stop(self) -> None:
        """停止插件运行时"""
        pass

    @abc.abstractmethod
    async def invoke_stream(
        self,
        invoke_request: dict[str, Any],
        timeout: int | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        流式调用插件方法

        """
        pass

    @abc.abstractmethod
    async def get_metrics(self) -> dict[str, Any]:
        """获取运行时指标"""
        pass

    @abc.abstractmethod
    async def get_logs(
        self, limit: int = 100, level: str | None = None
    ) -> list[dict[str, Any]]:
        """获取运行时日志"""
        pass

    def set_workspace_dir(self, workspace_dir: Path):
        """设置工作目录"""
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _update_state(self, new_state: str):
        """更新状态"""
        self._state = new_state

        if new_state == PluginRuntimeState.PREPARED:
            self._is_prepared = True
            self.prepared_at = datetime.now()
        elif new_state == PluginRuntimeState.RUNNING:
            self._is_running = True
            self.started_at = datetime.now()
        elif new_state == PluginRuntimeState.STOPPED:
            self._is_running = False
            self._is_stopping = False
            self.stopped_at = datetime.now()

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        return {
            "plugin_name": self.plugin_name,
            "state": self._state,
            "is_prepared": self._is_prepared,
            "is_running": self._is_running,
            "process_id": self.process_id,
            "port": self.port,
            "prepared_at": self.prepared_at.isoformat() if self.prepared_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "uptime": (datetime.now() - self.started_at).total_seconds()
            if self.started_at
            else 0,
        }

    def _get_plugin_logger(self) -> Logger:
        """获取带插件信息的logger包装器"""

        class PluginLoggerWrapper(Logger):
            """插件logger包装器，自动添加插件信息前缀"""

            def __init__(self, plugin_id: str, plugin_version: str):
                self.plugin_id = plugin_id
                self.plugin_version = plugin_version
                self.prefix = f"[插件:{plugin_id}@{plugin_version}] "

            def _log_with_prefix(self, level: str, message: str, *args, **kwargs):
                """在消息前添加插件信息前缀"""
                from loguru import logger as loguru_logger

                prefixed_message = self.prefix + message
                getattr(loguru_logger, level)(prefixed_message, *args, **kwargs)

            def trace(self, message: str, *args, **kwargs):
                self._log_with_prefix("trace", message, *args, **kwargs)

            def debug(self, message: str, *args, **kwargs):
                self._log_with_prefix("debug", message, *args, **kwargs)

            def info(self, message: str, *args, **kwargs):
                self._log_with_prefix("info", message, *args, **kwargs)

            def warning(self, message: str, *args, **kwargs):
                self._log_with_prefix("warning", message, *args, **kwargs)

            def error(self, message: str, *args, **kwargs):
                self._log_with_prefix("error", message, *args, **kwargs)

            def exception(self, message: str, *args, **kwargs):
                self._log_with_prefix("exception", message, *args, **kwargs)

            def critical(self, message: str, *args, **kwargs):
                self._log_with_prefix("critical", message, *args, **kwargs)

        return PluginLoggerWrapper(self.plugin_id, self.plugin_version)
