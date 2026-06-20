"""
租户模块分配 Schema
"""

from datetime import datetime

from framework.schemas import BaseModel
from pydantic import Field

# ============== 请求 Schema ==============

class AssignModuleRequest(BaseModel):
    """分配模块请求"""

    module_id: str = Field(..., description="模块ID")
    started_at: datetime = Field(..., description="生效时间")
    expired_at: datetime | None = Field(None, description="过期时间（可选）")

# ============== 响应 Schema ==============

class TenantModuleResponse(BaseModel):
    """租户模块响应"""

    id: str = Field(..., description="分配记录ID")
    tenant_id: str = Field(..., description="租户ID")
    module_id: str = Field(..., description="模块ID")
    module_code: str = Field(..., description="模块编码")
    module_name: str = Field(..., description="模块名称")
    module_is_need: bool = Field(..., description="是否必须模块")
    started_at: datetime = Field(..., description="生效时间")
    expired_at: datetime | None = Field(None, description="过期时间")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

class TenantModulePaginatedListResponse(BaseModel):
    """租户模块分页列表响应"""

    items: list[TenantModuleResponse] = Field(default_factory=list, description="模块列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")
