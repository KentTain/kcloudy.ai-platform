"""元数据 Schema"""

from datetime import datetime

from pydantic import Field

from framework.schemas import BaseModel, BasePaginatedQuery


class MetadataFieldDefine(BaseModel):
    """定义元数据字段请求"""

    name: str = Field(..., description="字段名称")
    field_type: str = Field(..., description="字段类型")
    is_required: bool = Field(default=False, description="是否必填")
    enum_values: list[str] | None = Field(default=None, description="枚举值")
    sort_order: int = Field(default=0, description="排序")


class MetadataSet(BaseModel):
    """设置元数据请求"""

    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    field_id: str = Field(..., description="字段ID")
    field_name: str = Field(..., description="字段名称")
    value: str | None = Field(default=None, description="值")


class MetadataBatchSet(BaseModel):
    """批量设置元数据请求"""

    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    items: list[MetadataSet] = Field(default_factory=list, description="元数据项")


class MetadataSearchQuery(BasePaginatedQuery):
    """元数据搜索查询"""

    library_id: str = Field(..., description="文档库ID")
    field_name: str = Field(..., description="字段名称")
    value: str = Field(..., description="值")
    resource_type: str | None = Field(default=None, description="资源类型")


class MetadataFieldResponse(BaseModel):
    """元数据字段响应"""

    id: str
    library_id: str
    name: str
    field_type: str
    is_required: bool = False
    enum_values: list[str] | None = None
    sort_order: int = 0
    created_at: datetime


class ResourceMetadataResponse(BaseModel):
    """资源元数据响应"""

    id: str
    library_id: str
    resource_type: str
    resource_id: str
    field_id: str
    field_name: str
    value: str | None = None
    created_at: datetime
