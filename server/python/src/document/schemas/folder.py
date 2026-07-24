"""文件夹 Schema"""

from datetime import datetime

from pydantic import Field

from framework.schemas import BaseModel


class FolderCreate(BaseModel):
    """创建文件夹请求"""

    library_id: str = Field(..., description="文档库ID")
    name: str = Field(..., description="文件夹名称")
    parent_id: str | None = Field(default=None, description="父文件夹ID")
    description: str | None = Field(default=None, description="描述")


class FolderRename(BaseModel):
    """重命名文件夹请求"""

    name: str = Field(..., description="新名称")


class FolderMove(BaseModel):
    """移动文件夹请求"""

    new_parent_id: str = Field(..., description="目标父文件夹ID")


class FolderResponse(BaseModel):
    """文件夹响应"""

    id: str
    library_id: str
    name: str
    parent_id: str | None = None
    description: str | None = None
    tree_level: int = 0
    tree_leaf: bool = True
    parent_ids: str = ""
    tree_sort: int = 0
    tree_sorts: str = ""
    tree_names: str = ""
    created_at: datetime
