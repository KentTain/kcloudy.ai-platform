"""tree_util edge cases 单元测试"""

import pytest

from demo.utils.tree_util import TreeUtil


class TreeNode:
    """测试用树节点"""

    def __init__(
        self,
        id: int,
        name: str,
        parent_id: int | None = None,
        sort: int = 0,
    ):
        self.id = id
        self.name = name
        self.parent_id = parent_id
        self.sort = sort
        self.parent_ids: str = ""
        self.tree_level: int = 0
        self.tree_sorts: str = ""
        self.tree_names: str = ""
        self.tree_leaf: bool = True


class TestTreeUtilEdgeCases:
    """TreeUtil 边界情况测试"""

    @pytest.mark.asyncio
    async def test_build_parameter_tree_root_with_no_children(self):
        """测试根节点没有子节点"""
        root = TreeNode(id=1, name="root", sort=1)

        await TreeUtil.build_parameter_tree(root, [root])

        assert root.tree_leaf is True
        assert root.tree_names == "root"

    @pytest.mark.asyncio
    async def test_build_parameter_tree_multiple_children(self):
        """测试根节点有多个子节点"""
        root = TreeNode(id=1, name="root", sort=1)
        child1 = TreeNode(id=2, name="child1", parent_id=1, sort=1)
        child2 = TreeNode(id=3, name="child2", parent_id=1, sort=2)
        child3 = TreeNode(id=4, name="child3", parent_id=1, sort=3)

        nodes = [root, child1, child2, child3]
        await TreeUtil.build_parameter_tree(root, nodes)

        assert root.tree_leaf is False
        assert len([n for n in nodes if n.parent_id == 1]) == 3

    @pytest.mark.asyncio
    async def test_build_parameter_tree_deep_nesting(self):
        """测试深层嵌套"""
        nodes = []
        for i in range(10):
            parent_id = i - 1 if i > 0 else None
            nodes.append(TreeNode(id=i, name=f"node{i}", parent_id=parent_id, sort=i))

        await TreeUtil.build_parameter_tree(nodes[0], nodes)

        # Verify each level
        for i in range(10):
            assert nodes[i].tree_level == i

    @pytest.mark.asyncio
    async def test_build_parameter_tree_single_child_only(self):
        """测试只有一个子节点"""
        root = TreeNode(id=1, name="root", sort=1)
        child = TreeNode(id=2, name="child", parent_id=1, sort=1)

        nodes = [root, child]
        await TreeUtil.build_parameter_tree(root, nodes)

        assert root.tree_leaf is False
        assert child.tree_leaf is True
        assert child.tree_level == 1

    def test_build_tree_with_none_parent(self):
        """测试父节点为None的情况"""
        nodes = [
            {"id": "1", "parent_id": None, "name": "root"},
            {"id": "2", "parent_id": "1", "name": "child"},
        ]

        result = TreeUtil.build_tree(nodes, parent_id=None)

        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_build_tree_with_zero_parent(self):
        """测试父节点为0的情况"""
        nodes = [
            {"id": "1", "parent_id": 0, "name": "root"},
            {"id": "2", "parent_id": "1", "name": "child"},
        ]

        result = TreeUtil.build_tree(nodes, parent_id=0)

        assert len(result) == 1

    def test_build_tree_with_special_characters(self):
        """测试包含特殊字符的节点名"""
        nodes = [
            {"id": "1", "parent_id": "", "name": "根节点"},
            {"id": "2", "parent_id": "1", "name": "子节点@#$%"},
        ]

        result = TreeUtil.build_tree(nodes, parent_id="")

        assert result[0]["name"] == "根节点"
        assert result[0]["children"][0]["name"] == "子节点@#$%"

    def test_build_tree_with_empty_string_parent(self):
        """测试父节点为空字符串"""
        nodes = [
            {"id": "1", "parent_id": "", "name": "root"},
            {"id": "2", "parent_id": "", "name": "orphan"},
        ]

        result = TreeUtil.build_tree(nodes, parent_id="")

        # Both should be roots
        assert len(result) == 2

    def test_build_tree_with_numeric_ids(self):
        """测试使用数字ID"""
        nodes = [
            {"id": 1, "parent_id": "", "name": "root"},
            {"id": 2, "parent_id": 1, "name": "child"},
            {"id": 3, "parent_id": 1, "name": "child2"},
            {"id": 4, "parent_id": 2, "name": "grandchild"},
        ]

        result = TreeUtil.build_tree(nodes, parent_id="")

        assert len(result) == 1
        assert len(result[0]["children"]) == 2

    def test_build_tree_circular_reference_handling(self):
        """测试循环引用的处理（应该不会无限循环）"""
        nodes = [
            {"id": "1", "parent_id": "2", "name": "node1"},
            {"id": "2", "parent_id": "1", "name": "node2"},
        ]

        # Should handle gracefully without infinite loop
        result = TreeUtil.build_tree(nodes, parent_id="")

        # Returns empty or partial result
        assert isinstance(result, list)

    def test_build_tree_with_duplicated_ids(self):
        """测试重复ID的处理"""
        nodes = [
            {"id": "1", "parent_id": "", "name": "first"},
            {"id": "1", "parent_id": "", "name": "second"},
        ]

        result = TreeUtil.build_tree(nodes, parent_id="")

        # Should handle gracefully
        assert isinstance(result, list)
