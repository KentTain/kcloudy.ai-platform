"""
用户端系统设置 Schema
"""

from datetime import datetime

from pydantic import BaseModel, Field

from framework.schemas import (
    BasePaginatedQuery,
    BaseQuery,
    PropertyAttributeVoMixin,
    PropertyVoMixin,
)


class ConsoleSystemSettingQuery(BaseQuery):
    """用户端系统设置查询参数"""

    pass


class ConsoleSystemSettingPaginatedQuery(ConsoleSystemSettingQuery, BasePaginatedQuery):
    """用户端系统设置分页查询参数"""

    pass


class ConsoleSystemSettingAttributeResponse(PropertyAttributeVoMixin):
    """用户端属性值响应"""

    id: str = Field(..., description="属性值ID")
    setting_id: str = Field(..., description="配置ID")


class ConsoleSystemSettingResponse(PropertyVoMixin):
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


class ConsoleSystemSettingPaginatedListResponse(BaseModel):
    """用户端系统设置分页列表响应"""

    items: list[ConsoleSystemSettingResponse] = Field(
        default_factory=list, description="设置列表"
    )
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")
