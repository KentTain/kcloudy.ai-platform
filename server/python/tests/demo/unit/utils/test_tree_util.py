"""tree_util 单元测试"""

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


class TestTreeUtil:
    """TreeUtil 单元测试"""

    @pytest.mark.asyncio
    async def test_build_parameter_tree_single_node(self):
        """测试单个节点的情况"""
        root = TreeNode(id=1, name="single", sort=1)

        await TreeUtil.build_parameter_tree(root, [root])

        assert root.tree_level == 0
        assert root.tree_leaf is True
        assert root.parent_ids == ""
        assert root.tree_names == "single"
        assert root.tree_sorts == "0000000001,"

    @pytest.mark.asyncio
    async def test_build_parameter_tree_two_levels(self):
        """测试两层树形结构"""
        root = TreeNode(id=1, name="root", sort=1)
        child1 = TreeNode(id=2, name="child1", parent_id=1, sort=1)
        child2 = TreeNode(id=3, name="child2", parent_id=1, sort=2)

        nodes = [root, child1, child2]
        await TreeUtil.build_parameter_tree(root, nodes)

        # 验证根节点
        assert root.tree_level == 0
        assert root.tree_leaf is False
        assert root.tree_names == "root"

        # 验证子节点
        assert child1.tree_level == 1
        assert child1.tree_leaf is True
        assert child1.parent_ids == "1"
        assert child1.tree_names == "root/child1"

        assert child2.tree_level == 1
        assert child2.tree_leaf is True
        assert child2.parent_ids == "1"
        assert child2.tree_names == "root/child2"

    @pytest.mark.asyncio
    async def test_build_parameter_tree_three_levels(self):
        """测试三层树形结构"""
        root = TreeNode(id=1, name="root", sort=1)
        child1 = TreeNode(id=2, name="child1", parent_id=1, sort=1)
        child2 = TreeNode(id=3, name="child2", parent_id=1, sort=2)
        grandchild1 = TreeNode(id=4, name="grandchild1", parent_id=2, sort=1)
        grandchild2 = TreeNode(id=5, name="grandchild2", parent_id=2, sort=2)

        nodes = [root, child1, child2, grandchild1, grandchild2]
        await TreeUtil.build_parameter_tree(root, nodes)

        # 验证根节点
        assert root.tree_level == 0
        assert root.tree_leaf is False
        assert root.tree_names == "root"

        # 验证第二层
        assert child1.tree_level == 1
        assert child1.tree_leaf is False
        assert child1.tree_names == "root/child1"
        assert child1.tree_sorts == "0000000001,0000000001,"

        assert child2.tree_level == 1
        assert child2.tree_leaf is True
        assert child2.tree_names == "root/child2"
        assert child2.tree_sorts == "0000000001,0000000002,"

        # 验证第三层
        assert grandchild1.tree_level == 2
        assert grandchild1.tree_leaf is True
        assert grandchild1.parent_ids == "1,2"
        assert grandchild1.tree_names == "root/child1/grandchild1"
        assert grandchild1.tree_sorts == "0000000001,0000000001,0000000001,"

        assert grandchild2.tree_level == 2
        assert grandchild2.tree_leaf is True
        assert grandchild2.parent_ids == "1,2"
        assert grandchild2.tree_names == "root/child1/grandchild2"

    def test_build_tree_with_dict_nodes(self):
        """测试使用字典节点构建树"""
        nodes = [
            {"id": "1", "parent_id": "", "name": "root"},
            {"id": "2", "parent_id": "1", "name": "child1"},
            {"id": "3", "parent_id": "1", "name": "child2"},
        ]

        result = TreeUtil.build_tree(nodes, parent_id="")

        assert len(result) == 1
        assert result[0]["id"] == "1"
        assert len(result[0]["children"]) == 2

    def test_build_tree_empty_list(self):
        """测试空列表"""
        result = TreeUtil.build_tree([])
        assert result == []

    def test_build_tree_with_transform_func(self):
        """测试使用转换函数"""

        def transform(node):
            return {"id": node["id"], "name": node["name"].upper()}

        nodes = [
            {"id": "1", "parent_id": "", "name": "root"},
            {"id": "2", "parent_id": "1", "name": "child"},
        ]

        result = TreeUtil.build_tree(nodes, parent_id="", transform_func=transform)

        assert result[0]["name"] == "ROOT"
        assert result[0]["children"][0]["name"] == "CHILD"
