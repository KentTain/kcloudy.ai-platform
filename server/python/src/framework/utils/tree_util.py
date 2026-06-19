"""
树形结构工具函数

提供通用的树构建方法，支持字典和对象两种数据源。
"""

from collections.abc import Callable
from typing import Any


class TreeUtil:
    """树形结构工具类"""

    DEFAULT_ROOT_ID = ""

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
            构建好的树形结构
        """
        if not tree_list:
            return []

        normalized_parent_id = None if parent_id is None else str(parent_id)

        result = []
        for tree_node in tree_list:
            node_parent_id = cls._get_parent_id(tree_node)

            if node_parent_id == normalized_parent_id:
                node_id = cls._get_node_id(tree_node)
                children = cls.build_tree(tree_list, node_id, transform_func)

                if transform_func:
                    transformed_node = transform_func(tree_node)
                    cls._set_children(transformed_node, children)
                    result.append(transformed_node)
                else:
                    cls._set_children(tree_node, children)
                    result.append(tree_node)

        return result

    @classmethod
    async def build_parameter_tree(
        cls,
        root: Any,
        nodes: list[Any],
    ) -> None:
        """
        构建参数树，设置节点的 tree_level、tree_leaf、parent_ids、tree_names、tree_sorts 属性

        Args:
            root: 根节点
            nodes: 所有节点列表
        """
        # 构建节点映射
        node_map = {cls._get_node_id(node): node for node in nodes}

        # 递归设置节点属性
        await cls._build_parameter_tree_recursive(
            root, nodes, level=0, parent_ids="", tree_names="", tree_sorts=""
        )

    @classmethod
    async def _build_parameter_tree_recursive(
        cls,
        node: Any,
        nodes: list[Any],
        level: int,
        parent_ids: str,
        tree_names: str,
        tree_sorts: str,
    ) -> None:
        """递归构建参数树"""
        node_id = cls._get_node_id(node)
        node_name = cls._get_node_name(node)
        node_sort = cls._get_node_sort(node)

        # 设置当前节点属性
        node.tree_level = level
        node.parent_ids = parent_ids
        node.tree_names = tree_names + node_name if tree_names else node_name
        node.tree_sorts = tree_sorts + f"{node_sort:010d},"

        # 找到子节点
        children = [n for n in nodes if cls._get_parent_id(n) == node_id]

        if children:
            node.tree_leaf = False
            new_parent_ids = f"{parent_ids},{node_id}" if parent_ids else str(node_id)
            new_tree_names = node.tree_names
            new_tree_sorts = node.tree_sorts

            for child in children:
                await cls._build_parameter_tree_recursive(
                    child,
                    nodes,
                    level=level + 1,
                    parent_ids=new_parent_ids,
                    tree_names=new_tree_names + "/",
                    tree_sorts=new_tree_sorts,
                )
        else:
            node.tree_leaf = True

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
    def _get_node_name(cls, node: Any) -> str:
        """获取节点名称"""
        if isinstance(node, dict):
            return str(node.get("name", ""))
        elif hasattr(node, "name"):
            return str(node.name)
        else:
            return ""

    @classmethod
    def _get_node_sort(cls, node: Any) -> int:
        """获取节点排序值"""
        if isinstance(node, dict):
            return int(node.get("sort", 0))
        elif hasattr(node, "sort"):
            return int(node.sort)
        else:
            return 0

    @classmethod
    def _get_parent_id(cls, node: Any) -> Any:
        """获取父节点ID"""
        if isinstance(node, dict):
            parent_id = node.get("parent_id", "")
        else:
            parent_id = getattr(node, "parent_id", "")
        if parent_id is None:
            return None
        return str(parent_id)

    @classmethod
    def _set_children(cls, node: Any, children: list[Any]) -> None:
        """设置子节点"""
        if isinstance(node, dict):
            node["children"] = children
        else:
            try:
                node.children = children
            except (AttributeError, TypeError):
                from loguru import logger
                _logger = logger.bind(name=__name__)
                _logger.debug(f"无法为 {type(node).__name__} 对象设置children属性")
