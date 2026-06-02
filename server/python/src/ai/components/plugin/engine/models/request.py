"""
请求和响应相关的数据模型定义
"""

from typing import Any

from pydantic import BaseModel, Field


class InstallRequest(BaseModel):
    """插件安装请求"""

    force: bool = Field(default=False, description="是否强制安装（覆盖已存在）")
    auto_start: bool = Field(default=True, description="安装后是否自动启动")
    config_override: dict[str, Any] = Field(default={}, description="配置覆盖")
