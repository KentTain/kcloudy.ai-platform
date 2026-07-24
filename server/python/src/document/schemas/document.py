"""文档 Schema"""

from datetime import datetime

from pydantic import Field

from framework.schemas import BaseModel, BasePaginatedQuery


class DocumentPaginatedQuery(BasePaginatedQuery):
    """文档分页查询"""

    library_id: str = Field(..., description="文档库ID")
    folder_id: str | None = Field(default=None, description="文件夹ID")


class DocumentMove(BaseModel):
    """移动文档请求"""

    target_folder_id: str | None = Field(default=None, description="目标文件夹ID")


class DocumentResponse(BaseModel):
    """文档响应"""

    id: str
    library_id: str
    folder_id: str | None = None
    owner_id: str
    name: str
    document_type: str = "document"
    lifecycle_status: str
    file_size: int = 0
    mime_type: str | None = None
    processing_status: str = "none"
    storage_key: str | None = None
    created_at: datetime
