"""
用户端系统设置 Schema
"""

from datetime import datetime

from pydantic import BaseModel, Field

from framework.common.schemas import PropertyAttributeVoMixin, PropertyVoMixin, VoMixin


class ConsoleSystemSettingAttributeResponse(VoMixin, PropertyAttributeVoMixin):
    """用户端属性值响应"""

    id: str = Field(..., description="属性值ID")
    setting_id: str = Field(..., description="配置ID")


class ConsoleSystemSettingResponse(VoMixin, PropertyVoMixin):
    """用户端系统设置响应"""

    id: str = Field(..., description="设置ID")
    tenant_id: str = Field(..., description="租户ID")
    code: str = Field(..., description="设置编号")
    application_id: str | None = Field(None, description="应用程序Id")
    application_name: str | None = Field(None, description="应用程序名称")
    attributes: list[ConsoleSystemSettingAttributeResponse] = Field(
        default_factory=list, description="属性值列表"
    )
    created_at: datetime = Field(..., description="创建时间")


class ConsoleSystemSettingListVo(BaseModel):
    """用户端系统设置列表响应"""

    items: list[ConsoleSystemSettingResponse] = Field(
        default_factory=list, description="设置列表"
    )
    total: int = Field(..., description="总数")
