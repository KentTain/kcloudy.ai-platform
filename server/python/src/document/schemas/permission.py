"""权限配置 Schema"""

from datetime import datetime

from pydantic import Field

from framework.schemas import BaseModel


class LibraryRoleCreate(BaseModel):
    """创建权限组请求"""

    code: str = Field(..., description="权限组编码")
    name: str = Field(..., description="权限组名称")
    description: str | None = Field(default=None, description="描述")


class LibraryRoleMemberAdd(BaseModel):
    """添加权限组成员请求"""

    user_id: str = Field(..., description="用户ID")


class ResourceAclCreate(BaseModel):
    """创建资源 ACL 请求"""

    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    subject_id: str = Field(..., description="授权对象ID")
    subject_type: str = Field(default="user", description="授权对象类型")
    action: str = Field(default="read", description="操作")
    effect: str = Field(default="allow", description="效果")
    priority: int = Field(default=0, description="优先级")


class InheritanceUpdate(BaseModel):
    """更新权限继承请求"""

    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    inherit_enabled: bool = Field(..., description="是否启用继承")


class LibraryRoleResponse(BaseModel):
    """权限组响应"""

    id: str
    library_id: str
    role_kind: str
    code: str
    name: str
    description: str | None = None
    permissions: dict = Field(default_factory=dict, description="权限定义")
    created_at: datetime


class LibraryRoleMemberResponse(BaseModel):
    """权限组成员响应"""

    id: str
    library_id: str
    role_id: str
    user_id: str
    created_at: datetime


class ResourceAclResponse(BaseModel):
    """资源 ACL 响应"""

    id: str
    library_id: str
    resource_type: str
    resource_id: str
    subject_id: str
    subject_type: str = "user"
    action: str = "read"
    effect: str = "allow"
    priority: int = 0
    inherited_from_resource_id: str | None = None
    created_at: datetime
