"""
插件定义 Schema

用于管理后台展示插件定义的响应模型。
"""

from __future__ import annotations

from framework.schemas import BaseModel
from pydantic import Field


class PluginDefinitionResponse(BaseModel):
    """插件定义响应"""

    id: str = Field(..., description="记录ID")
    plugin_id: str = Field(..., description="插件ID")
    plugin_unique_identifier: str = Field(..., description="插件唯一标识符")
    refers: int = Field(..., description="引用租户数")
    install_type: str = Field(..., description="安装类型")
    manifest_type: str | None = Field(None, description="清单类型")
    created_at: str | None = Field(None, description="创建时间")
    updated_at: str | None = Field(None, description="更新时间")
