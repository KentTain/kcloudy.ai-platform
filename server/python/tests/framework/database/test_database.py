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
from framework.database.mixins.tree import TreeMixin


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

    def test_tree_mixin_attributes(self):
        """
        场景：树结构混入属性
        WHEN: 检查 TreeMixin
        THEN: 包含正确属性
        """
        assert hasattr(TreeMixin, "parent_id")
        assert hasattr(TreeMixin, "level")
        assert hasattr(TreeMixin, "path")

    def test_tree_mixin_is_root(self):
        """
        场景：判断根节点
        WHEN: parent_id 为 None
        THEN: is_root 返回 True
        """
        # 创建一个模拟对象
        class MockTree(TreeMixin):
            def __init__(self):
                self.parent_id = None
                self.path = None

        node = MockTree()
        assert node.is_root() is True

    def test_tree_mixin_get_ancestors(self):
        """
        场景：获取祖先节点
        WHEN: path 有值
        THEN: 返回正确的 ID 列表
        """
        class MockTree(TreeMixin):
            def __init__(self, path):
                self.path = path

        node = MockTree("1,2,3,4")
        assert node.get_ancestors() == ["1", "2", "3", "4"]

    def test_tree_mixin_get_ancestors_empty(self):
        """
        场景：空路径
        WHEN: path 为 None
        THEN: 返回空列表
        """
        class MockTree(TreeMixin):
            def __init__(self):
                self.path = None

        node = MockTree()
        assert node.get_ancestors() == []
