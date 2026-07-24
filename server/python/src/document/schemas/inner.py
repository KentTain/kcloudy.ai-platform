"""内部接口 Schema"""

from pydantic import Field

from framework.schemas import BaseModel


class DocumentPermissionQuery(BaseModel):
    """文档权限查询"""

    document_id: str = Field(..., description="文档ID")
    user_id: str = Field(..., description="用户ID")


class MemberCheckQuery(BaseModel):
    """成员检查查询"""

    library_id: str = Field(..., description="文档库ID")
    user_id: str = Field(..., description="用户ID")


class PermissionApplyCallbackRequest(BaseModel):
    """权限申请回调请求"""

    request_type: str = Field(..., description="申请类型: library_join/library_resource/library_role")
    target_resource_id: str = Field(..., description="目标资源ID")
    applicant_id: str = Field(..., description="申请人ID")
    requested_role: str | None = Field(default=None, description="申请角色")
    requested_permission: str | None = Field(default=None, description="申请权限")
    extra_data: dict = Field(default_factory=dict, description="额外数据")
