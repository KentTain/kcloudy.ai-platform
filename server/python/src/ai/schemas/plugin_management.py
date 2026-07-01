"""
插件管理 Inner API Schema

提供插件管理相关的请求/响应模型，用于模块间 Inner API 通信。
"""

from typing import Any

from framework.schemas import BaseModel
from pydantic import Field


class InstallationItem(BaseModel):
    """单个插件安装项"""

    tenant_id: str = Field(..., description="租户ID")
    plugin_id: str = Field(..., description="插件ID")
    plugin_unique_identifier: str = Field(..., description="插件唯一标识符")
    declaration: dict[str, Any] = Field(..., description="插件声明配置")
    auto_start: bool = Field(default=False, description="是否自动启动")


class BatchInstallRequest(BaseModel):
    """批量安装插件请求"""

    installations: list[InstallationItem] = Field(..., description="安装项列表")


class InstallSuccessItem(BaseModel):
    """安装成功项"""

    tenant_id: str = Field(..., description="租户ID")
    plugin_id: str = Field(..., description="插件ID")


class InstallFailedItem(BaseModel):
    """安装失败项"""

    tenant_id: str = Field(..., description="租户ID")
    message: str = Field(..., description="失败原因")


class InstallSkippedItem(BaseModel):
    """安装跳过项"""

    tenant_id: str = Field(..., description="租户ID")
    reason: str = Field(..., description="跳过原因")


class BatchInstallResponse(BaseModel):
    """批量安装插件响应"""

    success: list[InstallSuccessItem] = Field(
        default_factory=list, description="成功列表"
    )
    failed: list[InstallFailedItem] = Field(
        default_factory=list, description="失败列表"
    )
    skipped: list[InstallSkippedItem] = Field(
        default_factory=list, description="跳过列表"
    )


class StartPluginResponse(BaseModel):
    """启动插件响应"""

    plugin_id: str = Field(..., description="插件ID")
    message: str = Field(..., description="响应消息")
    status: str = Field(..., description="插件状态")
    success: bool = Field(..., description="操作是否成功")
    process_id: int | None = Field(default=None, description="进程ID")
    port: int | None = Field(default=None, description="运行端口")


class StopPluginResponse(BaseModel):
    """停止插件响应"""

    plugin_id: str = Field(..., description="插件ID")
    message: str = Field(..., description="响应消息")
    status: str = Field(..., description="插件状态")
    success: bool = Field(..., description="操作是否成功")
