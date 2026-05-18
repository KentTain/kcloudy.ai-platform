"""
树形结构工具函数
"""

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class TreeNodeProtocol:
    """树节点协议，定义树节点需要实现的属性"""

    id: Any
    parent_id: Any | None
    name: str
    tree_level: int
    tree_sorts: str
    tree_names: str
    tree_leaf: bool
    sort: int


class TreeUtil:
    """树形结构工具类"""

    DEFAULT_ROOT_ID = ""

    @classmethod
    async def build_parameter_tree(cls, parent: Any, param_list: list[Any]) -> None:
        """
        递归构建参数树形结构

        Args:
            parent: 父节点
            param_list: 参数列表，用于查找子节点
        """
        # 设置根节点的名称和排序
        if parent.tree_level == 0:
            if not parent.tree_names:
                parent.tree_names = parent.name
            if not parent.tree_sorts and parent.sort is not None:
                parent.tree_sorts = f"{parent.sort:010d},"

        # 查找所有子节点
        children = [p for p in param_list if p.parent_id == parent.id]

        # 如果有子节点，设置父节点为非叶子节点
        if children:
            parent.tree_leaf = False

        # 递归处理所有子节点
        for child in children:
            # 设置父ID路径
            if parent.parent_ids:
                child.parent_ids = f"{parent.parent_ids},{parent.id}"
            else:
                child.parent_ids = str(parent.id)

            # 计算层级
            child.tree_level = parent.tree_level + 1

            # 设置排序路径
            child.tree_sorts = parent.tree_sorts + str(child.sort or 0).zfill(10) + ","

            # 设置名称路径
            if parent.tree_names:
                child.tree_names = f"{parent.tree_names}/{child.name}"
            else:
                child.tree_names = child.name

            # 递归处理子节点
            await cls.build_parameter_tree(child, param_list)

    @classmethod
    def build_tree(
        cls,
        tree_list: list[Any],
        parent_id: Any = DEFAULT_ROOT_ID,
        transform_func: Callable[[Any], Any] | None = None,
    ) -> list[Any]:
        """
        通用树构建方法

        Args:
            tree_list: 树节点列表
            parent_id: 父节点ID，默认为根节点ID
            transform_func: 可选的转换函数，用于在构建树时转换节点对象

        Returns:
            List[Any]: 构建好的树形结构
        """
        if not tree_list:
            return []

        # Normalize parent_id for consistent comparison
        normalized_parent_id = None if parent_id is None else str(parent_id)

        result = []
        for tree_node in tree_list:
            # 过滤父节点与传递的parent_id相同的TreeNode对象
            node_parent_id = cls._get_parent_id(tree_node)

            if node_parent_id == normalized_parent_id:
                # 递归设置子节点
                node_id = cls._get_node_id(tree_node)
                children = cls.build_tree(tree_list, node_id, transform_func)

                # 如果提供了转换函数，先转换节点再设置子节点
                if transform_func:
                    transformed_node = transform_func(tree_node)
                    cls._set_children(transformed_node, children)
                    result.append(transformed_node)
                else:
                    cls._set_children(tree_node, children)
                    result.append(tree_node)

        return result

    @classmethod
    def _get_node_id(cls, node: Any) -> str:
        """智能获取节点ID"""
        if isinstance(node, dict):
            return str(node.get("param_id", node.get("id", "")))
        elif hasattr(node, "param_id"):
            return str(node.param_id)
        elif hasattr(node, "id"):
            return str(node.id)
        else:
            return str(getattr(node, "id", ""))

    @classmethod
    def _get_parent_id(cls, node: Any) -> Any:
        """获取父节点ID"""
        if isinstance(node, dict):
            parent_id = node.get("parent_id", "")
        else:
            parent_id = getattr(node, "parent_id", "")
        # Return None as-is for proper comparison, otherwise convert to string
        if parent_id is None:
            return None
        return str(parent_id)

    @classmethod
    def _set_children(cls, node: Any, children: list[Any]) -> None:
        """设置子节点"""
        if isinstance(node, dict):
            # 字典类型：直接设置
            node["children"] = children
        else:
            # 对象类型：尝试设置children属性
            try:
                node.children = children
            except (AttributeError, TypeError):
                # 如果无法设置，记录调试信息但不中断程序
                from loguru import logger

                _logger = logger.bind(name=__name__)
                _logger.debug(f"无法为 {type(node).__name__} 对象设置children属性")
