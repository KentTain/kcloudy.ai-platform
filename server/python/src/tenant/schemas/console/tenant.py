"""
用户端租户 Schema
"""

from framework.schemas import BaseModel
from pydantic import Field

class UserTenantResponse(BaseModel):
    """用户租户响应"""
    id: str = Field(..., description="租户ID")
    name: str = Field(..., description="租户名称")
    code: str = Field(..., description="租户编码")
    status: str = Field(..., description="状态")
    role: str = Field(..., description="用户角色")
    is_default: bool = Field(..., description="是否默认租户")

class CurrentTenantResponse(BaseModel):
    """当前租户响应"""
    id: str = Field(..., description="租户ID")
    name: str = Field(..., description="租户名称")
    code: str = Field(..., description="租户编码")
    status: str = Field(..., description="状态")

class SwitchTenantResponse(BaseModel):
    """切换租户响应"""
    tenant_id: str = Field(..., description="租户ID")
    tenant_name: str = Field(..., description="租户名称")
    message: str = Field(..., description="提示消息")
