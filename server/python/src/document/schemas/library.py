"""文档库 Schema"""

from datetime import datetime

from pydantic import Field

from framework.schemas import BaseModel, BasePaginatedQuery


class LibraryCreate(BaseModel):
    """创建文档库请求"""

    library_type: str = Field(..., description="文档库类型")
    code: str = Field(..., description="编码")
    name: str = Field(..., description="名称")
    description: str | None = Field(default=None, description="描述")
    icon: str | None = Field(default=None, description="图标")


class LibraryUpdate(BaseModel):
    """更新文档库请求"""

    name: str | None = Field(default=None, description="名称")
    description: str | None = Field(default=None, description="描述")
    icon: str | None = Field(default=None, description="图标")
    enabled: bool | None = Field(default=None, description="是否启用")
    allow_submit_to_kb: bool | None = Field(default=None, description="允许提交到知识库")


class LibraryPaginatedQuery(BasePaginatedQuery):
    """文档库分页查询"""

    library_type: str | None = Field(default=None, description="文档库类型")


class LibraryResponse(BaseModel):
    """文档库响应"""

    id: str
    type: str
    code: str
    name: str
    description: str | None = None
    icon: str | None = None
    owner_id: str
    enabled: bool
    allow_submit_to_kb: bool
    created_at: datetime
