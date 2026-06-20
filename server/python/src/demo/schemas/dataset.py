"""
Dataset Pydantic Schemas
"""

from datetime import datetime

from framework.schemas import BaseModel
from pydantic import Field


class DatasetCreate(BaseModel):
    """创建知识库请求"""

    name: str = Field(..., min_length=1, max_length=255, description="知识库名称")
    description: str | None = Field(None, description="知识库描述")


class DatasetUpdate(BaseModel):
    """更新知识库请求"""

    name: str | None = Field(
        None, min_length=1, max_length=255, description="知识库名称"
    )
    description: str | None = Field(None, description="知识库描述")


class DatasetResponse(BaseModel):
    """知识库视图对象"""

    id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class DatasetPaginatedListResponse(BaseModel):
    """知识库分页列表响应"""

    total: int
    page: int
    page_size: int
    items: list[DatasetResponse]
