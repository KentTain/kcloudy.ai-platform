"""
GraphRAG GraphData 模型测试

验证 GraphData 模型的数据验证和字段定义。

测试覆盖：
- 模型创建
- 可选字段处理
- 默认值验证
- 数据类型验证
"""


from ai.components.graphrag.client import GraphData


class TestGraphDataModel:
    """GraphData 模型测试"""

    def test_create_empty_instance(self):
        """测试创建空实例"""
        # GraphData 所有字段都有默认值（None 或指定默认值）
        data = GraphData()
        assert data is not None
        assert isinstance(data, GraphData)

    def test_create_with_title(self):
        """测试创建带标题的实例"""
        data = GraphData(title="Test Entity")
        assert data.title == "Test Entity"

    def test_create_with_type(self):
        """测试创建带类型的实例"""
        data = GraphData(type="person")
        assert data.type == "person"

    def test_create_with_degree(self):
        """测试创建带 degree 的实例"""
        data = GraphData(degree=10)
        assert data.degree == 10

    def test_create_with_description(self):
        """测试创建带描述的实例"""
        data = GraphData(description="This is a test entity")
        assert data.description == "This is a test entity"

    def test_create_with_source_target(self):
        """测试创建带源和目标的实例（关系类型）"""
        data = GraphData(source="Entity A", target="Entity B", weight=5)
        assert data.source == "Entity A"
        assert data.target == "Entity B"
        assert data.weight == 5

    def test_create_with_id(self):
        """测试创建带 ID 的实例"""
        data = GraphData(id="entity-123")
        assert data.id == "entity-123"

    def test_create_with_community(self):
        """测试创建带社区的实例"""
        data = GraphData(community="community-1")
        assert data.community == "community-1"

    def test_create_with_level(self):
        """测试创建带级别的实例"""
        data = GraphData(level=2)
        assert data.level == 2

    def test_create_with_custom_fields(self):
        """测试创建带自定义字段的实例"""
        data = GraphData(custom_add="add-123", custom_update="update-456")
        assert data.custom_add == "add-123"
        assert data.custom_update == "update-456"


class TestGraphDataDefaults:
    """GraphData 默认值测试"""

    def test_default_values(self):
        """测试默认值"""
        data = GraphData()

        # 大多数字段默认为 None
        assert data.title is None
        assert data.type is None
        assert data.degree is None
        assert data.description is None
        assert data.source is None
        assert data.target is None
        assert data.weight is None
        assert data.rank is None
        assert data.id is None
        assert data.summary is None
        assert data.full_content is None

        # community 和 level 有非 None 默认值
        assert data.community == "1"
        assert data.level == 1

        # 自定义字段默认为 None
        assert data.custom_add is None
        assert data.custom_update is None

    def test_community_default_value(self):
        """测试 community 默认值"""
        data = GraphData()
        assert data.community == "1"

    def test_level_default_value(self):
        """测试 level 默认值"""
        data = GraphData()
        assert data.level == 1


class TestGraphDataTypes:
    """GraphData 数据类型测试"""

    def test_integer_field_types(self):
        """测试整数字段类型"""
        data = GraphData(
            degree=10,
            weight=5,
            rank=3,
            level=2
        )

        assert isinstance(data.degree, int)
        assert isinstance(data.weight, int)
        assert isinstance(data.rank, int)
        assert isinstance(data.level, int)

    def test_string_field_types(self):
        """测试字符串字段类型"""
        data = GraphData(
            title="Test",
            type="entity",
            description="Description",
            source="A",
            target="B",
            id="123",
            community="comm-1",
            summary="Summary",
            full_content="Content"
        )

        assert isinstance(data.title, str)
        assert isinstance(data.type, str)
        assert isinstance(data.description, str)
        assert isinstance(data.source, str)
        assert isinstance(data.target, str)
        assert isinstance(data.id, str)
        assert isinstance(data.community, str)
        assert isinstance(data.summary, str)
        assert isinstance(data.full_content, str)

    def test_type_coercion_for_integer_fields(self):
        """测试整数字段的类型转换"""
        # Pydantic 会自动转换兼容类型
        data = GraphData(
            degree="10",  # 字符串数字
            weight=5.0,  # 浮点数
            level="2"    # 字符串数字
        )

        # Pydantic 会转换为整数
        assert data.degree == 10
        assert data.weight == 5
        assert data.level == 2


class TestGraphDataValidation:
    """GraphData 数据验证测试"""

    def test_model_dump(self):
        """测试模型序列化"""
        data = GraphData(
            title="Test Entity",
            type="person",
            degree=10,
            community="community-1",
            level=2
        )

        # 序列化为字典
        data_dict = data.model_dump()

        assert data_dict["title"] == "Test Entity"
        assert data_dict["type"] == "person"
        assert data_dict["degree"] == 10
        assert data_dict["community"] == "community-1"
        assert data_dict["level"] == 2

    def test_model_dump_exclude_none(self):
        """测试模型序列化排除 None 值"""
        data = GraphData(
            title="Test Entity",
            type="person"
        )

        # 序列化为字典，排除 None 值
        data_dict = data.model_dump(exclude_none=True)

        # 只包含非 None 值
        assert "title" in data_dict
        assert "type" in data_dict
        assert "degree" not in data_dict  # None，被排除
        assert "description" not in data_dict  # None，被排除

    def test_model_json_serialization(self):
        """测试模型 JSON 序列化"""
        data = GraphData(
            title="Test Entity",
            type="person",
            degree=10
        )

        # 序列化为 JSON
        json_str = data.model_dump_json()

        assert '"title":"Test Entity"' in json_str
        assert '"type":"person"' in json_str
        assert '"degree":10' in json_str


class TestGraphDataFields:
    """GraphData 字段完整性测试"""

    def test_all_fields_exist(self):
        """测试所有字段存在"""
        expected_fields = [
            "title",
            "type",
            "degree",
            "description",
            "source",
            "target",
            "weight",
            "rank",
            "id",
            "summary",
            "full_content",
            "community",
            "level",
            "custom_add",
            "custom_update",
        ]

        data = GraphData()
        for field in expected_fields:
            assert hasattr(data, field), f"缺少字段: {field}"

    def test_field_count(self):
        """测试字段数量"""
        data = GraphData()
        # 获取所有字段名称
        field_names = data.model_fields.keys()
        # GraphData 有 15 个字段
        assert len(field_names) == 15
