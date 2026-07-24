"""标签 Schema"""

from datetime import datetime

from pydantic import Field

from framework.schemas import BaseModel, BasePaginatedQuery


class TagCreate(BaseModel):
    """创建标签请求"""

    name: str = Field(..., description="标签名称")
    group_id: str | None = Field(default=None, description="分组ID")
    color: str | None = Field(default=None, description="颜色")
    description: str | None = Field(default=None, description="描述")
    persona_id: str | None = Field(default=None, description="关联人设ID")


class TagPaginatedQuery(BasePaginatedQuery):
    """标签分页查询"""

    group_id: str | None = Field(default=None, description="分组ID")


class TagResponse(BaseModel):
    """标签响应"""

    id: str
    name: str
    group_id: str | None = None
    color: str | None = None
    description: str | None = None
    persona_id: str | None = None
    doc_count: int = 0
    created_at: datetime


class TagGroupResponse(BaseModel):
    """标签分组响应"""

    id: str
    name: str
    sort_order: int = 0
    created_at: datetime
