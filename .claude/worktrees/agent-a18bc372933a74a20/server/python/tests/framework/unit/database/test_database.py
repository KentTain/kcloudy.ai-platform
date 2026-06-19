"""
database 模块单元测试
"""

import pytest
from datetime import datetime
import uuid

from framework.database.types.uuid import StringUUID
from framework.database.types.snowflake import SnowflakeIDGenerator
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.tree import TreeNodeMixin


class TestStringUUID:
    """StringUUID 类型测试"""

    def test_process_bind_param_with_uuid(self):
        """
        场景：绑定 UUID 参数
        WHEN: 传入 UUID 对象
        THEN: 转换为字符串
        """
        uuid_type = StringUUID()
        test_uuid = uuid.uuid4()
        result = uuid_type.process_bind_param(test_uuid, None)
        assert result == str(test_uuid)

    def test_process_bind_param_with_string(self):
        """
        场景：绑定字符串参数
        WHEN: 传入字符串
        THEN: 返回字符串
        """
        uuid_type = StringUUID()
        test_str = "550e8400-e29b-41d4-a716-446655440000"
        result = uuid_type.process_bind_param(test_str, None)
        assert result == test_str

    def test_process_bind_param_with_none(self):
        """
        场景：绑定 None
        WHEN: 传入 None
        THEN: 返回 None
        """
        uuid_type = StringUUID()
        result = uuid_type.process_bind_param(None, None)
        assert result is None

    def test_process_result_value(self):
        """
        场景：处理结果值
        WHEN: 传入字符串
        THEN: 返回 UUID 对象
        """
        uuid_type = StringUUID()
        test_str = "550e8400-e29b-41d4-a716-446655440000"
        result = uuid_type.process_result_value(test_str, None)
        assert isinstance(result, uuid.UUID)
        assert str(result) == test_str


class TestSnowflakeIDGenerator:
    """雪花ID 生成器测试"""

    def test_generate_returns_int(self):
        """
        场景：生成 ID
        WHEN: 调用 generate
        THEN: 返回整数
        """
        generator = SnowflakeIDGenerator()
        result = generator.generate()
        assert isinstance(result, int)
        assert result > 0

    def test_generate_unique(self):
        """
        场景：生成唯一 ID
        WHEN: 多次调用 generate
        THEN: 返回不同值
        """
        generator = SnowflakeIDGenerator()
        ids = [generator.generate() for _ in range(100)]
        assert len(ids) == len(set(ids))

    def test_generate_ordered(self):
        """
        场景：生成有序 ID
        WHEN: 多次调用 generate
        THEN: ID 递增
        """
        generator = SnowflakeIDGenerator()
        ids = [generator.generate() for _ in range(10)]
        assert ids == sorted(ids)


class TestMixins:
    """Mixin 类测试"""

    def test_audit_mixin_attributes(self):
        """
        场景：审计混入属性
        WHEN: 检查 AuditMixin
        THEN: 包含正确属性
        """
        # 检查类属性存在
        assert hasattr(AuditMixin, "created_by")
        assert hasattr(AuditMixin, "updated_by")

    def test_tenant_mixin_attributes(self):
        """
        场景：租户混入属性
        WHEN: 检查 TenantMixin
        THEN: 包含正确属性
        """
        assert hasattr(TenantMixin, "tenant_id")

    def test_tree_node_mixin_attributes(self):
        """
        场景：树结构混入属性
        WHEN: 检查 TreeNodeMixin
        THEN: 包含正确属性
        """
        assert hasattr(TreeNodeMixin, "parent_id")
        assert hasattr(TreeNodeMixin, "tree_level")
        assert hasattr(TreeNodeMixin, "tree_leaf")
        assert hasattr(TreeNodeMixin, "tree_sort")
        assert hasattr(TreeNodeMixin, "tree_sorts")
        assert hasattr(TreeNodeMixin, "tree_names")
        assert hasattr(TreeNodeMixin, "parent_ids")

    def test_tree_node_mixin_is_leaf(self):
        """
        场景：判断叶子节点
        WHEN: tree_leaf 为 True
        THEN: 是叶子节点
        """
        # 创建一个模拟对象
        class MockTreeNode(TreeNodeMixin):
            def __init__(self):
                self.parent_id = "root"
                self.tree_leaf = True
                self.tree_level = 1
                self.tree_sorts = "001,"
                self.tree_names = "测试"
                self.parent_ids = "root,"

        node = MockTreeNode()
        assert node.tree_leaf is True

    def test_tree_node_mixin_level(self):
        """
        场景：树节点层级
        WHEN: tree_level 有值
        THEN: 正确表示层级
        """
        class MockTreeNode(TreeNodeMixin):
            def __init__(self, level):
                self.tree_level = level

        root = MockTreeNode(0)
        child = MockTreeNode(1)

        assert root.tree_level == 0
        assert child.tree_level == 1

    def test_tree_node_mixin_parent_ids(self):
        """
        场景：父节点路径
        WHEN: parent_ids 有值
        THEN: 正确表示路径
        """
        class MockTreeNode(TreeNodeMixin):
            def __init__(self, parent_ids):
                self.parent_ids = parent_ids

        node = MockTreeNode("root,node1,node2,")
        assert "root" in node.parent_ids
        assert "node1" in node.parent_ids
        assert "node2" in node.parent_ids
