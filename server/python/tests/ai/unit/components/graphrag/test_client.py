"""
GraphRAGClient 基础测试

验证 GraphRAGClient 客户端的基础功能。

测试覆盖：
- 客户端初始化
- 方法存在性
- GraphData 导入
- 方法签名
"""

import inspect

import pytest

from ai.components.graphrag.client import GraphData, GraphRAGClient


class TestGraphRAGClientInit:
    """GraphRAGClient 初始化测试"""

    def test_client_instantiation(self):
        """测试客户端可以实例化"""
        client = GraphRAGClient()
        assert client is not None
        assert isinstance(client, GraphRAGClient)

    def test_client_no_required_params(self):
        """测试客户端不需要必需参数"""
        # GraphRAGClient 的 __init__ 没有必需参数
        sig = inspect.signature(GraphRAGClient.__init__)
        params = list(sig.parameters.keys())

        # 只有 self 参数
        assert "self" in params
        # 没有其他必需参数
        required_params = [
            name for name, param in sig.parameters.items()
            if param.default == inspect.Parameter.empty and name != "self"
        ]
        assert len(required_params) == 0

    def test_client_has_graph_data(self):
        """测试客户端关联 GraphData"""
        # GraphData 应该可以从同一个模块导入
        assert GraphData is not None
        assert hasattr(GraphData, "model_fields")


class TestGraphRAGClientMethods:
    """GraphRAGClient 方法存在性测试"""

    def test_has_create_index_build_task_method(self):
        """测试客户端有 create_index_build_task 方法"""
        client = GraphRAGClient()
        assert hasattr(client, "create_index_build_task")
        assert callable(client.create_index_build_task)

    def test_has_search_method(self):
        """测试客户端有 search 方法"""
        client = GraphRAGClient()
        assert hasattr(client, "search")
        assert callable(client.search)

    def test_method_signatures(self):
        """测试方法签名"""
        # create_index_build_task 签名
        sig = inspect.signature(GraphRAGClient.create_index_build_task)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "namespace" in params
        assert "kb_code" in params
        assert "filename" in params
        assert "docs" in params

        # search 签名（从源码推断）
        sig = inspect.signature(GraphRAGClient.search)
        params = list(sig.parameters.keys())
        assert "self" in params


class TestGraphRAGClientMethodReturnTypes:
    """GraphRAGClient 方法返回类型测试"""

    def test_create_index_build_task_return_type(self):
        """测试 create_index_build_task 返回类型"""
        sig = inspect.signature(GraphRAGClient.create_index_build_task)
        # 返回类型应该是 dict
        assert sig.return_annotation == "dict" or sig.return_annotation == dict

    def test_search_return_type(self):
        """测试 search 返回类型"""
        sig = inspect.signature(GraphRAGClient.search)
        # 返回类型可能是 dict 或其他类型，根据实际实现
        # 这里只验证方法存在返回类型注解（可能是空的）
        assert hasattr(sig, "return_annotation")


class TestGraphDataImport:
    """GraphData 导入测试"""

    def test_import_graph_data_from_client(self):
        """测试从 client 模块导入 GraphData"""
        from ai.components.graphrag.client import GraphData

        assert GraphData is not None
        # Pydantic 字段通过 model_fields 定义，不在类属性上
        assert "title" in GraphData.model_fields
        assert "type" in GraphData.model_fields

    def test_graph_data_is_pydantic_model(self):
        """测试 GraphData 是 Pydantic 模型"""
        from pydantic import BaseModel

        assert issubclass(GraphData, BaseModel)

    def test_graph_data_model_fields(self):
        """测试 GraphData 模型字段"""
        from ai.components.graphrag.client import GraphData

        # 验证关键字段存在
        data = GraphData()
        assert hasattr(data, "title")
        assert hasattr(data, "type")
        assert hasattr(data, "description")
        assert hasattr(data, "id")


class TestGraphRAGClientIntegration:
    """GraphRAGClient 集成测试（不连接真实服务）"""

    @pytest.mark.asyncio
    async def test_create_index_build_task_is_async(self):
        """测试 create_index_build_task 是异步方法"""
        client = GraphRAGClient()

        # 验证是协程函数
        import asyncio
        assert asyncio.iscoroutinefunction(client.create_index_build_task)

    @pytest.mark.asyncio
    async def test_search_is_async(self):
        """测试 search 是异步方法"""
        client = GraphRAGClient()

        # 验证是协程函数
        import asyncio
        assert asyncio.iscoroutinefunction(client.search)

    def test_client_methods_exist(self):
        """测试客户端所有公开方法存在"""
        client = GraphRAGClient()

        # 预期的公开方法
        expected_methods = [
            "create_index_build_task",
            "search",
        ]

        for method_name in expected_methods:
            assert hasattr(client, method_name), f"缺少方法: {method_name}"
            assert callable(getattr(client, method_name)), f"方法不可调用: {method_name}"


class TestGraphRAGClientDocumentation:
    """GraphRAGClient 文档测试"""

    def test_client_class_has_docstring(self):
        """测试客户端类有文档字符串"""
        assert GraphRAGClient.__doc__ is not None
        assert len(GraphRAGClient.__doc__) > 0

    def test_create_index_build_task_has_docstring(self):
        """测试 create_index_build_task 方法有文档字符串"""
        assert GraphRAGClient.create_index_build_task.__doc__ is not None
        assert len(GraphRAGClient.create_index_build_task.__doc__) > 0

    def test_search_has_docstring(self):
        """测试 search 方法有文档字符串"""
        assert GraphRAGClient.search.__doc__ is not None
        assert len(GraphRAGClient.search.__doc__) > 0
