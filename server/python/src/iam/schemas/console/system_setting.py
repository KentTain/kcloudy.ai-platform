"""
用户端系统设置 Schema
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConsoleSystemSettingAttributeResponse(BaseModel):
    """用户端属性值响应"""

    model_config = {"from_attributes": True}

    id: str = Field(..., description="属性值ID")
    setting_id: str = Field(..., description="配置ID")
    data_type: str = Field(..., description="属性数据类型")
    name: str = Field(..., description="属性值名称")
    display_name: str | None = Field(None, description="显示名称")
    description: str | None = Field(None, description="描述")
    value: str | None = Field(None, description="属性值")
    ext_data: dict[str, Any] | None = Field(None, description="扩展数据")
    can_edit: bool = Field(..., description="是否能编辑")
    is_require: bool = Field(..., description="是否必须")
    index: int = Field(..., description="排序")


class ConsoleSystemSettingResponse(BaseModel):
    """用户端系统设置响应"""

    model_config = {"from_attributes": True}

    id: str = Field(..., description="设置ID")
    tenant_id: str = Field(..., description="租户ID")
    code: str = Field(..., description="设置编号")
    name: str = Field(..., description="名称")
    display_name: str | None = Field(None, description="显示名称")
    description: str | None = Field(None, description="描述")
    application_id: str | None = Field(None, description="应用程序Id")
    application_name: str | None = Field(None, description="应用程序名称")
    can_edit: bool = Field(..., description="是否能编辑")
    is_require: bool = Field(..., description="是否必须")
    index: int = Field(..., description="排序")
    attributes: list[ConsoleSystemSettingAttributeResponse] = Field(default_factory=list, description="属性值列表")
    created_at: datetime = Field(..., description="创建时间")


class ConsoleSystemSettingListVo(BaseModel):
    """用户端系统设置列表响应"""

    items: list[ConsoleSystemSettingResponse] = Field(default_factory=list, description="设置列表")
    total: int = Field(..., description="总数")
