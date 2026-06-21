"""
菜单相关 Pydantic Schemas
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from framework.schemas import BaseModel, TreeNodeTreeVo
from pydantic import Field

if TYPE_CHECKING:
    from iam.models import Menu


class MenuTreeNode(TreeNodeTreeVo):
    """菜单树节点视图对象"""

    module: str = Field(..., description="所属模块标识")
    code: str = Field(..., description="菜单编码")
    name: str = Field(..., description="菜单名称")
    path: str = Field(..., description="前端路由路径")
    icon: str | None = Field(None, description="图标标识")
    is_visible: bool = Field(True, description="是否显示")
    deployment_base_url: str | None = Field(None, description="模块部署地址")

    @classmethod
    def from_menu(cls, menu: "Menu") -> "MenuTreeNode":
        """从 Menu 实体构建 MenuTreeNode

        Args:
            menu: Menu 实体对象

        Returns:
            MenuTreeNode 实例
        """
        return cls(
            id=menu.id,
            parent_id=menu.parent_id,
            parent_ids=menu.parent_ids,
            tree_leaf=menu.tree_leaf,
            tree_sorts=menu.tree_sorts,
            tree_names=menu.tree_names,
            module=menu.module,
            code=menu.code,
            name=menu.name,
            path=menu.path,
            icon=menu.icon,
            is_visible=menu.is_visible,
            deployment_base_url=menu.deployment_base_url,
        )


class MenuListResponse(BaseModel):
    """菜单列表响应"""

    menus: list[MenuTreeNode] = Field(default_factory=list, description="菜单树列表")
