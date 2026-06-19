"""
菜单相关 Pydantic Schemas
"""

from pydantic import BaseModel, Field

from framework.schemas.tree import TreeNodeTreeVo


class MenuTreeNode(TreeNodeTreeVo):
    """菜单树节点视图对象"""

    module: str = Field(..., description="所属模块标识")
    code: str = Field(..., description="菜单编码")
    name: str = Field(..., description="菜单名称")
    path: str = Field(..., description="前端路由路径")
    icon: str | None = Field(None, description="图标标识")
    is_visible: bool = Field(True, description="是否显示")
    deployment_base_url: str | None = Field(None, description="模块部署地址")


class MenuListResponse(BaseModel):
    """菜单列表响应"""

    menus: list[MenuTreeNode] = Field(default_factory=list, description="菜单树列表")
