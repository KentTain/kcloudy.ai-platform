"""
BaseConnect 接口测试

验证 BaseConnect 抽象基类的接口定义正确。

测试覆盖：
- 抽象基类定义
- 抽象方法完整性
- 方法签名验证
- 子类实现约束
"""

from abc import ABC
from inspect import isabstract

import pytest

from ai.components.datasource.interfaces import BaseConnect


class TestBaseConnectInterface:
    """BaseConnect 接口测试"""

    def test_is_abstract_class(self):
        """验证 BaseConnect 是抽象基类"""
        assert issubclass(BaseConnect, ABC)
        assert isabstract(BaseConnect)

    def test_cannot_instantiate_directly(self):
        """验证不能直接实例化抽象基类"""
        with pytest.raises(TypeError):
            BaseConnect()  # type: ignore

    def test_abstract_methods_exist(self):
        """验证所有抽象方法存在"""
        expected_methods = [
            "get_show_create_table",
            "get_example_data",
            "get_table_names",
            "get_table_info",
            "get_database_names",
            "get_table_comments",
            "get_table_comment",
            "get_columns",
            "get_column_comments",
            "get_fields",
            "get_indexes",
            "get_index_info",
            "run",
            "run_to_df",
        ]

        for method_name in expected_methods:
            assert hasattr(BaseConnect, method_name), f"缺少方法: {method_name}"

    def test_abstract_methods_count(self):
        """验证抽象方法数量"""
        abstract_methods = BaseConnect.__abstractmethods__
        # 预期有 14 个抽象方法
        assert len(abstract_methods) == 14

    def test_get_simple_fields_is_concrete(self):
        """验证 get_simple_fields 不是抽象方法（有默认实现）"""
        assert "get_simple_fields" not in BaseConnect.__abstractmethods__
        assert hasattr(BaseConnect, "get_simple_fields")

    def test_method_signatures(self):
        """验证方法签名正确"""
        import inspect

        # 验证 get_show_create_table 签名
        sig = inspect.signature(BaseConnect.get_show_create_table)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "table_name" in params

        # 验证 get_example_data 签名
        sig = inspect.signature(BaseConnect.get_example_data)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "table_name" in params
        assert "count" in params

        # 验证 run 签名
        sig = inspect.signature(BaseConnect.run)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "command" in params
        assert "fetch" in params

        # 验证 run_to_df 签名
        sig = inspect.signature(BaseConnect.run_to_df)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "command" in params
        assert "fetch" in params


class TestBaseConnectImplementation:
    """BaseConnect 实现约束测试"""

    def test_incomplete_implementation_raises_error(self):
        """验证不完整的实现会引发错误"""

        class IncompleteConnect(BaseConnect):
            """不完整的实现"""
            pass

        with pytest.raises(TypeError):
            IncompleteConnect()  # type: ignore

    def test_complete_implementation_can_instantiate(self):
        """验证完整实现可以实例化"""

        class CompleteConnect(BaseConnect):
            """完整实现"""

            async def get_show_create_table(self, table_name: str) -> str:
                return f"CREATE TABLE {table_name} ..."

            async def get_example_data(self, table_name: str, count: int = 3) -> list[dict]:
                return [{"id": 1}]

            async def get_table_names(self):
                return ["table1", "table2"]

            async def get_table_info(self, table_names: list[str] | None = None) -> str:
                return "table info"

            async def get_database_names(self) -> list[str]:
                return ["db1", "db2"]

            async def get_table_comments(self) -> list[tuple[str, str]]:
                return [("table1", "comment1")]

            async def get_table_comment(self, table_name: str) -> dict:
                return {"text": "comment"}

            async def get_columns(self, table_name: str) -> list[dict]:
                return [{"name": "id"}]

            async def get_column_comments(self, table_name: str) -> list[tuple[str, str]]:
                return [("id", "ID column")]

            async def get_fields(self, table_name: str) -> list[tuple[str, str, str, str, str]]:
                return [("id", "int", "", "true", "ID")]

            async def get_indexes(self, table_name: str) -> list[dict]:
                return [{"name": "idx_id"}]

            async def get_index_info(self, table_names: list[str] | None = None) -> str:
                return "index info"

            async def run(self, command: str, fetch: str = "all") -> list:
                return []

            async def run_to_df(self, command: str, fetch: str = "all"):
                return None

        # 应该可以实例化
        instance = CompleteConnect()
        assert isinstance(instance, BaseConnect)
        assert isinstance(instance, ABC)
