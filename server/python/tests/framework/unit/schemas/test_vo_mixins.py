"""
VO Mixin 单元测试

测试 PropertyVoMixin、PropertyAttributeVoMixin 和 TreeNodeVo 的定义和行为。
"""

from datetime import datetime

from framework.schemas import (
    PropertyAttributeVoMixin,
    PropertyVoMixin,
    TreeNodeTreeVo,
    TreeNodeVo,
    VoMixin,
)
from framework.schemas.tree import TreeNodeVoMixin


class TestPropertyVoMixin:
    """测试 PropertyVoMixin"""

    def test_property_vo_mixin_inherits_vo_mixin(self):
        """PropertyVoMixin 必须继承 VoMixin"""
        assert issubclass(PropertyVoMixin, VoMixin)

    def test_property_vo_mixin_has_required_fields(self):
        """PropertyVoMixin 必须包含所有必需字段"""
        fields = PropertyVoMixin.model_fields
        assert "name" in fields
        assert "display_name" in fields
        assert "description" in fields
        assert "can_edit" in fields
        assert "is_require" in fields
        assert "index" in fields

    def test_property_vo_mixin_default_values(self):
        """PropertyVoMixin 默认值必须正确"""
        # 创建一个具体的 VO 类来测试默认值
        class ConcreteVo(PropertyVoMixin):
            pass

        instance = ConcreteVo(name="test")
        assert instance.name == "test"
        assert instance.display_name is None
        assert instance.description is None
        assert instance.can_edit is True
        assert instance.is_require is False
        assert instance.index == 0


class TestPropertyAttributeVoMixin:
    """测试 PropertyAttributeVoMixin"""

    def test_property_attribute_vo_mixin_inherits_vo_mixin(self):
        """PropertyAttributeVoMixin 必须继承 VoMixin"""
        assert issubclass(PropertyAttributeVoMixin, VoMixin)

    def test_property_attribute_vo_mixin_has_required_fields(self):
        """PropertyAttributeVoMixin 必须包含所有必需字段"""
        fields = PropertyAttributeVoMixin.model_fields
        assert "data_type" in fields
        assert "name" in fields
        assert "display_name" in fields
        assert "description" in fields
        assert "value" in fields
        assert "ext_data" in fields
        assert "can_edit" in fields
        assert "is_require" in fields
        assert "index" in fields

    def test_property_attribute_vo_mixin_default_values(self):
        """PropertyAttributeVoMixin 默认值必须正确"""
        class ConcreteVo(PropertyAttributeVoMixin):
            pass

        instance = ConcreteVo(name="test_attr")
        assert instance.data_type == "string"
        assert instance.name == "test_attr"
        assert instance.display_name is None
        assert instance.description is None
        assert instance.value is None
        assert instance.ext_data is None
        assert instance.can_edit is True
        assert instance.is_require is False
        assert instance.index == 0


class TestTreeNodeVo:
    """测试 TreeNodeVo"""

    def test_tree_node_vo_inherits_correctly(self):
        """TreeNodeVo 必须继承 VoMixin 和 TreeNodeVoMixin"""
        assert issubclass(TreeNodeVo, VoMixin)
        assert issubclass(TreeNodeVo, TreeNodeVoMixin)

    def test_tree_node_vo_has_id_field(self):
        """TreeNodeVo 必须包含 id 字段"""
        fields = TreeNodeVo.model_fields
        assert "id" in fields

    def test_tree_node_vo_serialization(self):
        """TreeNodeVo 序列化必须正确"""
        node = TreeNodeVo(
            id="node-1",
            parent_id="parent-1",
            tree_level=1,
            tree_leaf=False,
            tree_sort=1,
            tree_sorts="0.1",
            tree_names="root/child",
            parent_ids="root",
        )

        data = node.model_dump()
        assert data["id"] == "node-1"
        assert data["parent_id"] == "parent-1"
        assert data["tree_level"] == 1
        assert data["tree_leaf"] is False

    def test_tree_node_vo_from_attributes(self):
        """TreeNodeVo 必须支持 from_attributes"""

        # 模拟 ORM 对象
        class MockOrmObject:
            id = "orm-1"
            parent_id = None
            tree_level = 0
            tree_leaf = True
            tree_sort = 0
            tree_sorts = ""
            tree_names = ""
            parent_ids = ""

        node = TreeNodeVo.model_validate(MockOrmObject())
        assert node.id == "orm-1"
        assert node.parent_id is None
        assert node.tree_leaf is True


class TestTreeNodeTreeVo:
    """测试 TreeNodeTreeVo"""

    def test_tree_node_tree_vo_inherits_tree_node_vo(self):
        """TreeNodeTreeVo 必须继承 TreeNodeVo"""
        assert issubclass(TreeNodeTreeVo, TreeNodeVo)

    def test_tree_node_tree_vo_has_children(self):
        """TreeNodeTreeVo 必须包含 children 字段"""
        fields = TreeNodeTreeVo.model_fields
        assert "children" in fields

    def test_tree_node_tree_vo_nested_structure(self):
        """TreeNodeTreeVo 必须支持嵌套结构"""
        child = TreeNodeTreeVo(id="child-1", tree_leaf=True)
        parent = TreeNodeTreeVo(id="parent-1", children=[child], tree_leaf=False)

        assert len(parent.children) == 1
        assert parent.children[0].id == "child-1"
        assert parent.tree_leaf is False


class TestExports:
    """测试导出"""

    def test_property_vo_mixin_exported(self):
        """PropertyVoMixin 必须从 framework.schemas 导出"""
        from framework.schemas import PropertyVoMixin as ReImported

        assert PropertyVoMixin is ReImported

    def test_property_attribute_vo_mixin_exported(self):
        """PropertyAttributeVoMixin 必须从 framework.schemas 导出"""
        from framework.schemas import PropertyAttributeVoMixin as ReImported

        assert PropertyAttributeVoMixin is ReImported


class TestSystemSettingResponse:
    """测试重构后的 SystemSettingResponse"""

    def test_system_setting_response_uses_mixin(self):
        """SystemSettingResponse 必须使用 PropertyVoMixin"""
        from iam.schemas.admin.system_setting import SystemSettingResponse

        assert issubclass(SystemSettingResponse, PropertyVoMixin)
        assert issubclass(SystemSettingResponse, VoMixin)

    def test_system_setting_response_fields(self):
        """SystemSettingResponse 必须包含所有必需字段"""
        from iam.schemas.admin.system_setting import SystemSettingResponse

        fields = SystemSettingResponse.model_fields
        # 来自 PropertyVoMixin
        assert "name" in fields
        assert "display_name" in fields
        assert "description" in fields
        assert "can_edit" in fields
        assert "is_require" in fields
        assert "index" in fields
        # 业务字段
        assert "id" in fields
        assert "tenant_id" in fields
        assert "code" in fields
        assert "attributes" in fields

    def test_system_setting_attribute_response_uses_mixin(self):
        """SystemSettingAttributeResponse 必须使用 PropertyAttributeVoMixin"""
        from iam.schemas.admin.system_setting import SystemSettingAttributeResponse

        assert issubclass(SystemSettingAttributeResponse, PropertyAttributeVoMixin)
        assert issubclass(SystemSettingAttributeResponse, VoMixin)

    def test_system_setting_response_serialization(self):
        """SystemSettingResponse 序列化必须正确"""
        from iam.schemas.admin.system_setting import (
            SystemSettingAttributeResponse,
            SystemSettingResponse,
        )

        attr = SystemSettingAttributeResponse(
            id="attr-1",
            setting_id="setting-1",
            name="attr_name",
            data_type="string",
            value="attr_value",
            created_at=datetime.now(),
        )

        setting = SystemSettingResponse(
            id="setting-1",
            tenant_id="tenant-1",
            code="APP_CONFIG",
            name="应用配置",
            application_id=None,
            application_name=None,
            attributes=[attr],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        data = setting.model_dump()
        assert data["id"] == "setting-1"
        assert data["name"] == "应用配置"
        assert len(data["attributes"]) == 1
        assert data["attributes"][0]["name"] == "attr_name"
