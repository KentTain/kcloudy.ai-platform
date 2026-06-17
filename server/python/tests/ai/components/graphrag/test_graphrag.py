"""GraphRAG 组件测试"""

import pytest


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
        from pydantic import ValidationError

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
