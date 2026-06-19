"""GraphRAG 组件测试"""



class TestGraphData:
    """GraphData 模型测试"""

    def test_graph_data_creation(self):
        """测试 GraphData 模型创建"""
        from ai.components.graphrag.client import GraphData

        data = GraphData(
            title="测试实体",
            type="person",
            description="这是一个测试实体",
            degree=1,
            rank=1,
        )

        assert data.title == "测试实体"
        assert data.type == "person"
        assert data.description == "这是一个测试实体"
        assert data.degree == 1
        assert data.rank == 1

    def test_graph_data_optional_fields(self):
        """测试 GraphData 可选字段"""
        from ai.components.graphrag.client import GraphData

        # 只提供必需字段（实际上所有字段都是可选的）
        data = GraphData()

        # 验证默认值
        assert data.title is None
        assert data.type is None
        assert data.description is None
        assert data.community == "1"
        assert data.level == 1

    def test_graph_data_validation(self):
        """测试 GraphData 数据验证"""

        from ai.components.graphrag.client import GraphData

        # 验证有效数据
        valid_data = GraphData(
            title="有效标题",
            degree=10,
            weight=5,
        )
        assert valid_data.degree == 10
        assert valid_data.weight == 5

        # 验证字段类型转换
        data = GraphData(degree="5")  # 字符串应该被转换为整数
        assert data.degree == 5
        assert isinstance(data.degree, int)


class TestGraphRAGClient:
    """GraphRAGClient 基础测试"""

    def test_client_initialization(self):
        """测试客户端初始化"""
        from ai.components.graphrag.client import GraphRAGClient

        client = GraphRAGClient()
        assert client is not None

    def test_client_has_required_methods(self):
        """测试客户端有必需的方法"""
        from ai.components.graphrag.client import GraphRAGClient

        client = GraphRAGClient()

        # 验证关键方法存在
        assert hasattr(client, 'create_index_build_task')
        assert hasattr(client, 'search')
        assert callable(client.create_index_build_task)
        assert callable(client.search)

    def test_graph_data_model_import(self):
        """测试 GraphData 模型可从客户端导入"""
        from ai.components.graphrag.client import GraphData

        # 验证可以创建 GraphData 实例
        data = GraphData(title="导入测试")
        assert data.title == "导入测试"

    def test_graph_data_inheritance(self):
        """测试 GraphData 继承自 BaseModel"""
        from pydantic import BaseModel

        from ai.components.graphrag.client import GraphData

        assert issubclass(GraphData, BaseModel)
