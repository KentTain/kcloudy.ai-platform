"""回收站 Schema"""

from datetime import datetime

from pydantic import Field

from framework.schemas import BaseModel, BasePaginatedQuery


class RecyclePaginatedQuery(BasePaginatedQuery):
    """回收站分页查询"""

    library_id: str = Field(..., description="文档库ID")


class RecycleItemResponse(BaseModel):
    """回收站项目响应"""

    id: str
    library_id: str
    resource_type: str
    resource_id: str
    original_parent_id: str | None = None
    original_path: str | None = None
    deleted_by: str | None = None
    status: str
    created_at: datetime
