"""
管理后台系统设置 Schema
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from framework.schemas import PropertyAttributeVoMixin, PropertyVoMixin, BaseQuery, BasePaginatedQuery
from framework.database import AttributeDataType


# ============== 查询参数 Schema ==============


class SystemSettingQuery(BaseQuery):
    """系统设置查询参数"""

    pass


class SystemSettingPaginatedQuery(SystemSettingQuery, BasePaginatedQuery):
    """系统设置分页查询参数"""

    pass


# ============== 属性值 Schema ==============


class SystemSettingAttributeCreate(BaseModel):
    """属性值创建请求"""

    name: str = Field(..., min_length=1, max_length=256, description="属性值名称")
    display_name: str | None = Field(None, max_length=512, description="显示名称")
    description: str | None = Field(None, max_length=4000, description="描述")
    data_type: AttributeDataType = Field(
        default=AttributeDataType.STRING, description="属性数据类型"
    )
    value: str | None = Field(None, description="属性值")
    ext_data: dict[str, Any] | None = Field(None, description="扩展数据")
    can_edit: bool = Field(default=True, description="是否能编辑")
    is_require: bool = Field(default=False, description="是否必须")
    index: int = Field(default=0, ge=0, description="排序")


class SystemSettingAttributeResponse(PropertyAttributeVoMixin):
    """属性值响应"""

    id: str = Field(..., description="属性值ID")
    setting_id: str = Field(..., description="配置ID")
    created_at: datetime = Field(..., description="创建时间")


# ============== 系统设置 Schema ==============


class SystemSettingCreate(BaseModel):
    """系统设置创建请求"""

    code: str = Field(..., min_length=1, max_length=20, description="设置编号")
    name: str = Field(..., min_length=1, max_length=256, description="名称")
    display_name: str | None = Field(None, max_length=512, description="显示名称")
    description: str | None = Field(None, max_length=4000, description="描述")
    application_id: str | None = Field(None, max_length=36, description="应用程序Id")
    application_name: str | None = Field(None, max_length=128, description="应用程序名称")
    can_edit: bool = Field(default=True, description="是否能编辑")
    is_require: bool = Field(default=False, description="是否必须")
    index: int = Field(default=0, ge=0, description="排序")
    attributes: list[SystemSettingAttributeCreate] = Field(
        default_factory=list, description="属性值列表"
    )


class SystemSettingUpdate(BaseModel):
    """系统设置更新请求"""

    code: str | None = Field(None, min_length=1, max_length=20, description="设置编号")
    name: str | None = Field(None, min_length=1, max_length=256, description="名称")
    display_name: str | None = Field(None, max_length=512, description="显示名称")
    description: str | None = Field(None, max_length=4000, description="描述")
    application_id: str | None = Field(None, max_length=36, description="应用程序Id")
    application_name: str | None = Field(None, max_length=128, description="应用程序名称")
    can_edit: bool | None = Field(None, description="是否能编辑")
    is_require: bool | None = Field(None, description="是否必须")
    index: int | None = Field(None, ge=0, description="排序")
    attributes: list[SystemSettingAttributeCreate] | None = Field(
        None, description="属性值列表"
    )


class SystemSettingResponse(PropertyVoMixin):
    """系统设置响应"""

    id: str = Field(..., description="设置ID")
    tenant_id: str = Field(..., description="租户ID")
    code: str = Field(..., description="设置编号")
    application_id: str | None = Field(None, description="应用程序Id")
    application_name: str | None = Field(None, description="应用程序名称")
    attributes: list[SystemSettingAttributeResponse] = Field(
        default_factory=list, description="属性值列表"
    )
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class SystemSettingPaginatedListResponse(BaseModel):
    """系统设置分页列表响应"""

    items: list[SystemSettingResponse] = Field(
        default_factory=list, description="设置列表"
    )
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")
