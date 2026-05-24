"""
TreeNodeMixin 单元测试

测试 TreeNodeMixin 的树字段维护和 CRUD 方法。
"""

import pytest
import pytest_asyncio
from datetime import datetime
from typing import Any
from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from framework.database import Base
from framework.database.mixins.tree import TreeNodeMixin

# 所有测试函数都使用 asyncio
pytestmark = pytest.mark.asyncio


# ==================== 测试模型 ====================

class TestTreeNode(Base, TreeNodeMixin):
    """测试树节点模型"""

    __tablename__ = "test_tree_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4().hex), comment="ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="名称")

    @classmethod
    def tree_name_field(cls) -> str:
        """返回名称字段"""
        return "name"


# ==================== Fixtures ====================

@pytest_asyncio.fixture
async def engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """创建测试会话"""
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session


# ==================== 字段初始化测试 ====================

class TestTreeNodeMixinFieldInitialization:
    """测试树字段初始化"""

    async def test_root_node_field_initialization(self, session: AsyncSession):
        """测试根节点字段初始化"""
        # WHEN 创建根层节点（parent_id 为空或 DEFAULT_TREE_ROOT_ID）
        node = await TestTreeNode.create_node(session, {"name": "根节点"})

        # THEN tree_level 为 0
        assert node.tree_level == 0
        # THEN parent_ids 为 DEFAULT_TREE_ROOT_ID,
        assert node.parent_ids == "root,"
        # THEN tree_leaf 为 True
        assert node.tree_leaf is True
        # THEN tree_sorts 为排序号格式化后的字符串
        assert len(node.tree_sorts) == 9  # 8位数字 + 逗号
        # THEN tree_names 为节点名称
        assert node.tree_names == "根节点"

    async def test_child_node_field_initialization(self, session: AsyncSession):
        """测试子节点字段初始化"""
        # GIVEN 一个父节点
        parent = await TestTreeNode.create_node(session, {"name": "父节点"})

        # WHEN 创建子节点
        child = await TestTreeNode.create_node(
            session, {"name": "子节点", "parent_id": parent.id}
        )

        # THEN tree_level 为父节点 tree_level + 1
        assert child.tree_level == parent.tree_level + 1
        # THEN parent_ids 为 `父节点.parent_ids父节点.id,`
        assert child.parent_ids == f"{parent.parent_ids}{parent.id},"
        # THEN tree_sorts 为 `父节点.tree_sorts + 当前排序号格式化,`
        assert child.tree_sorts.startswith(parent.tree_sorts)
        # THEN tree_names 为 `父节点.tree_names/当前节点名称`
        assert child.tree_names == f"{parent.tree_names}/子节点"


# ==================== 创建节点测试 ====================

class TestTreeNodeMixinCreateNode:
    """测试创建节点"""

    async def test_create_root_node(self, session: AsyncSession):
        """测试创建根节点"""
        # WHEN 调用 create_node 且无 parent_id
        node = await TestTreeNode.create_node(session, {"name": "研发部"})

        # THEN 创建的节点 parent_id 为 DEFAULT_TREE_ROOT_ID
        assert node.parent_id == "root"
        # THEN tree_level 为 0
        assert node.tree_level == 0
        # THEN 自动计算并设置 tree_sort
        assert node.tree_sort >= 0

    async def test_create_child_node(self, session: AsyncSession):
        """测试创建子节点"""
        # GIVEN 一个父节点
        parent = await TestTreeNode.create_node(session, {"name": "研发部"})

        # WHEN 调用 create_node 并指定 parent_id
        child = await TestTreeNode.create_node(
            session, {"name": "前端组", "parent_id": parent.id}
        )

        # THEN 自动设置 tree_level、tree_sorts、tree_names、parent_ids
        assert child.tree_level == 1
        assert child.tree_sorts.startswith(parent.tree_sorts)
        assert child.tree_names == "研发部/前端组"
        assert parent.id in child.parent_ids

        # THEN 父节点的 tree_leaf 设置为 False
        await session.refresh(parent)
        assert parent.tree_leaf is False

    async def test_auto_assign_sort(self, session: AsyncSession):
        """测试自动分配排序号"""
        # GIVEN 一个父节点
        parent = await TestTreeNode.create_node(session, {"name": "研发部"})

        # WHEN 创建节点时未指定 tree_sort
        child1 = await TestTreeNode.create_node(
            session, {"name": "前端组", "parent_id": parent.id}
        )
        child2 = await TestTreeNode.create_node(
            session, {"name": "后端组", "parent_id": parent.id}
        )

        # THEN 自动分配为同级节点最大排序号 + DEFAULT_SORT
        assert child2.tree_sort > child1.tree_sort


# ==================== 更新节点测试 ====================

class TestTreeNodeMixinUpdateNode:
    """测试更新节点"""

    async def test_update_node_name(self, session: AsyncSession):
        """测试更新节点名称"""
        # GIVEN 一个节点
        node = await TestTreeNode.create_node(session, {"name": "研发部"})
        # GIVEN 一个子节点
        child = await TestTreeNode.create_node(
            session, {"name": "前端组", "parent_id": node.id}
        )

        # WHEN 更新节点名称
        updated = await TestTreeNode.update_node(session, node.id, {"name": "技术部"})

        # THEN 自动更新该节点的 tree_names
        assert updated.tree_names == "技术部"
        # THEN 级联更新所有子孙节点的 tree_names
        await session.refresh(child)
        assert child.tree_names == "技术部/前端组"

    async def test_move_node_to_new_parent(self, session: AsyncSession):
        """测试移动节点到新父节点"""
        # GIVEN 一个父节点
        parent1 = await TestTreeNode.create_node(session, {"name": "部门A"})
        # GIVEN 另一个父节点
        parent2 = await TestTreeNode.create_node(session, {"name": "部门B"})
        # GIVEN 一个子节点
        child = await TestTreeNode.create_node(
            session, {"name": "小组1", "parent_id": parent1.id}
        )

        # WHEN 更新节点的 parent_id
        updated = await TestTreeNode.update_node(
            session, child.id, {"parent_id": parent2.id}
        )

        # THEN 验证新父节点不是当前节点的子孙节点
        # THEN 自动更新该节点的 tree_level、tree_sorts、parent_ids
        assert updated.tree_level == 1
        assert updated.parent_id == parent2.id
        # THEN 刷新原父节点和新父节点的 tree_leaf 状态
        await session.refresh(parent1)
        await session.refresh(parent2)
        assert parent1.tree_leaf is True
        assert parent2.tree_leaf is False

    async def test_prevent_circular_reference(self, session: AsyncSession):
        """测试阻止循环引用"""
        # GIVEN 一个父节点
        parent = await TestTreeNode.create_node(session, {"name": "研发部"})
        # GIVEN 一个子节点
        child = await TestTreeNode.create_node(
            session, {"name": "前端组", "parent_id": parent.id}
        )

        # WHEN 尝试将父节点移动到子节点下
        # THEN 抛出异常
        with pytest.raises(ValueError, match="不能将节点移动到其子孙节点下"):
            await TestTreeNode.update_node(
                session, parent.id, {"parent_id": child.id}
            )


# ==================== 删除节点测试 ====================

class TestTreeNodeMixinDeleteNode:
    """测试删除节点"""

    async def test_delete_leaf_node(self, session: AsyncSession):
        """测试删除叶子节点"""
        # GIVEN 一个父节点
        parent = await TestTreeNode.create_node(session, {"name": "研发部"})
        # GIVEN 一个子节点
        child = await TestTreeNode.create_node(
            session, {"name": "前端组", "parent_id": parent.id}
        )

        # WHEN 删除叶子节点
        count = await TestTreeNode.delete_node(session, child.id)

        # THEN 仅删除该节点
        assert count == 1
        # THEN 刷新父节点的 tree_leaf 状态
        await session.refresh(parent)
        assert parent.tree_leaf is True

    async def test_delete_non_leaf_node(self, session: AsyncSession):
        """测试删除非叶子节点"""
        # GIVEN 一个父节点
        parent = await TestTreeNode.create_node(session, {"name": "研发部"})
        # GIVEN 一个子节点
        child = await TestTreeNode.create_node(
            session, {"name": "前端组", "parent_id": parent.id}
        )

        # WHEN 删除有子节点的节点
        count = await TestTreeNode.delete_node(session, parent.id)

        # THEN 级联删除所有子孙节点
        assert count == 2


# ==================== 列表查询测试 ====================

class TestTreeNodeMixinListNodes:
    """测试列表查询"""

    async def test_list_all_nodes(self, session: AsyncSession):
        """测试查询所有节点"""
        # GIVEN 多个节点
        node1 = await TestTreeNode.create_node(session, {"name": "研发部"})
        node2 = await TestTreeNode.create_node(
            session, {"name": "前端组", "parent_id": node1.id}
        )
        node3 = await TestTreeNode.create_node(session, {"name": "市场部"})

        # WHEN 调用 list_nodes
        nodes = await TestTreeNode.list_nodes(session)

        # THEN 返回按 tree_sorts 排序的节点列表
        assert len(nodes) == 3
        assert nodes[0].tree_sorts <= nodes[1].tree_sorts

    async def test_fuzzy_search(self, session: AsyncSession):
        """测试模糊查询"""
        # GIVEN 多个节点
        await TestTreeNode.create_node(session, {"name": "研发部"})
        await TestTreeNode.create_node(session, {"name": "研发中心"})
        await TestTreeNode.create_node(session, {"name": "市场部"})

        # WHEN 调用 list_nodes 并使用 fuzzy_fields
        nodes = await TestTreeNode.list_nodes(
            session, fuzzy_fields={"name": "研发"}
        )

        # THEN 返回名称包含"研发"的节点列表
        assert len(nodes) == 2
        for node in nodes:
            assert "研发" in node.name


# ==================== 树构建测试 ====================

class TestTreeNodeMixinBuildTree:
    """测试树构建"""

    async def test_build_full_tree(self, session: AsyncSession):
        """测试构建完整树"""
        # GIVEN 多个节点
        parent = await TestTreeNode.create_node(session, {"name": "研发部"})
        child = await TestTreeNode.create_node(
            session, {"name": "前端组", "parent_id": parent.id}
        )

        # WHEN 调用 build_tree
        nodes = await TestTreeNode.list_nodes(session)
        tree = TestTreeNode.build_tree(nodes)

        # THEN 返回树形结构，每个节点包含 children 列表
        assert len(tree) == 1
        assert tree[0]["id"] == parent.id
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["id"] == child.id

    async def test_build_subtree(self, session: AsyncSession):
        """测试构建子树"""
        # GIVEN 多个节点
        parent = await TestTreeNode.create_node(session, {"name": "研发部"})
        child = await TestTreeNode.create_node(
            session, {"name": "前端组", "parent_id": parent.id}
        )

        # WHEN 调用 build_tree 并指定 parent_id
        nodes = await TestTreeNode.list_nodes(session)
        tree = TestTreeNode.build_tree(nodes, parent_id=parent.id)

        # THEN 返回以指定节点为根的子树
        assert len(tree) == 1
        assert tree[0]["id"] == child.id
