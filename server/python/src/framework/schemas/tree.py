"""
树节点 VO 基类

提供统一的树节点响应格式。
"""

from pydantic import Field

from framework.common.schemas import TreeNodeVoMixin, VoMixin


class TreeNodeVo(VoMixin, TreeNodeVoMixin):
    """
    树节点 VO 基类

    继承 VoMixin 和 TreeNodeVoMixin，提供统一的树节点字段，用于 API 响应。
    """

    id: str
    # 覆盖默认值以保持 API 兼容性
    parent_ids: str = Field(default="", description="全父级id")
    tree_leaf: bool = Field(default=True, description="是否叶末")
    tree_sorts: str = Field(default="", description="多级排序号")
    tree_names: str = Field(default="", description="全节点名")


class TreeNodeTreeVo(TreeNodeVo):
    """
    树节点树形 VO 基类

    继承 TreeNodeVo，增加 children 字段，用于嵌套树结构响应。
    """

    children: list["TreeNodeTreeVo"] = []
