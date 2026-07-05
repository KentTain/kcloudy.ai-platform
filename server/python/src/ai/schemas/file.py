"""文件 Schema 模型"""

from __future__ import annotations

from framework.schemas import BaseModel
from pydantic import Field


class FileUploadResponse(BaseModel):
    """文件上传响应"""

    url: str = Field(..., description="文件访问 URL")
    media_type: str = Field(..., description="文件 MIME 类型")
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
