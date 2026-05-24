"""
树节点 VO 基类

提供统一的树节点响应格式。
"""

from typing import Any
from pydantic import BaseModel, ConfigDict


class TreeNodeVo(BaseModel):
    """
    树节点 VO 基类

    提供统一的树节点字段，用于 API 响应。
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    parent_id: str | None = None
    tree_level: int = 0
    tree_leaf: bool = True
    tree_sort: int = 0
    tree_sorts: str = ""
    tree_names: str = ""
    parent_ids: str = ""


class TreeNodeTreeVo(TreeNodeVo):
    """
    树节点树形 VO 基类

    继承 TreeNodeVo，增加 children 字段，用于嵌套树结构响应。
    """

    children: list["TreeNodeTreeVo"] = []