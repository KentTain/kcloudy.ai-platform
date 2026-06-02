"""
插件相关的数据模型定义
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# TODO: 任务 5 迁移 core/helper 后解除注释
# from ai.components.plugin.engine.core.helper import PluginConfig
# TODO: 任务 8 迁移 models/plugin 后解除注释
# from ai.models.plugin import PluginStatus


class PluginMetrics(BaseModel):
    """插件性能指标"""

    cpu_usage: float = Field(description="CPU使用率")
    memory_usage: float = Field(description="内存使用量（MB）")
    memory_percent: float = Field(description="内存使用率")
    disk_usage: float = Field(description="磁盘使用量（MB）")
    network_sent: float = Field(description="网络发送量（bytes）")
    network_recv: float = Field(description="网络接收量（bytes）")
    request_count: int = Field(default=0, description="请求次数")
    error_count: int = Field(default=0, description="错误次数")
    avg_response_time: float = Field(default=0.0, description="平均响应时间（ms）")
    uptime: float = Field(description="运行时间（秒）")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="最后更新时间"
    )


# TODO: 任务 5 和 8 完成后，解除 PluginInfo 类的注释
# class PluginInfo(BaseModel):
#     """插件信息"""
#
#     # 基本信息
#     id: str | None = Field(default=None, description="插件ID")
#     name: str | None = Field(default=None, description="插件名称")
#     version: str | None = Field(default=None, description="插件版本")
#
#     config: PluginConfig = Field(..., description="插件配置")
#     status: PluginStatus | None = Field(default=None, description="插件状态")
#     pid: int | None = Field(default=None, description="进程ID")
#     port: int | None = Field(default=None, description="监听端口")
#     work_dir: Path | None = Field(default=None, description="工作目录")
#     log_file: Path | None = Field(default=None, description="日志文件")
#     metrics: PluginMetrics | None = Field(default=None, description="性能指标")
#     error_message: str | None = Field(default=None, description="错误信息")
#
#     # 时间戳
#     installed_at: datetime | None = Field(default=None, description="安装时间")
#     started_at: datetime | None = Field(default=None, description="启动时间")
#     stopped_at: datetime | None = Field(default=None, description="停止时间")


class PluginEvent(BaseModel):
    """插件事件"""

    plugin_name: str = Field(description="插件名称")
    event_type: str = Field(description="事件类型")
    data: dict[str, Any] = Field(default={}, description="事件数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件时间")
