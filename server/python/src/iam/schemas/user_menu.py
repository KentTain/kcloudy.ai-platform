"""
用户菜单响应模型

定义用户菜单 API 的响应格式。
"""

from framework.schemas import BaseModel
from pydantic import Field


class UserMenuTreeResponse(BaseModel):
    """
    用户菜单视图对象

    用于返回用户有权限访问的菜单树。
    """

    id: str = Field(..., description="菜单ID")
    code: str = Field(..., description="菜单编码")
    name: str = Field(..., description="菜单名称")
    icon: str | None = Field(None, description="图标标识")
    path: str | None = Field(None, description="前端路由路径")
    sort_order: int = Field(0, description="排序号")
    is_visible: bool = Field(True, description="是否在侧边栏显示")
    children: list["UserMenuTreeResponse"] = Field(default_factory=list, description="子菜单列表")


class UserMenuListResponse(BaseModel):
    """
    用户菜单列表响应

    返回当前用户有权限的菜单树。
    """

    data: list[UserMenuTreeResponse] = Field(default_factory=list, description="菜单树列表")
