"""Datasource 组件测试"""

import pytest


class TestDatasourceImports:
    """Datasource 组件导入测试"""

    def test_import_interfaces(self):
        """测试导入 interfaces 模块"""
        from ai.components.datasource.interfaces import BaseConnect

        assert BaseConnect is not None
        assert hasattr(BaseConnect, "get_show_create_table")
        assert hasattr(BaseConnect, "get_example_data")

    def test_import_rdbms_base(self):
        """测试导入 rdbms.base 模块"""
        from ai.components.datasource.rdbms.base import RDBMSDatabase

        assert RDBMSDatabase is not None
        assert hasattr(RDBMSDatabase, "from_uri_db")

    def test_import_mysql_connect(self):
        """测试导入 MySQL 连接器"""
        from ai.components.datasource.rdbms.conn_mysql import MySQLConnect

        assert MySQLConnect is not None
        assert MySQLConnect.db_type == "mysql"
        assert MySQLConnect.driver == "mysql+aiomysql"


class TestBaseConnect:
    """BaseConnect 接口测试"""

    def test_base_connect_is_abstract(self):
        """测试 BaseConnect 是抽象类"""
        from ai.components.datasource.interfaces import BaseConnect
        from abc import ABC

        assert issubclass(BaseConnect, ABC)

        # 验证不能直接实例化
        with pytest.raises(TypeError):
            BaseConnect()

    def test_base_connect_has_required_methods(self):
        """测试 BaseConnect 有必需的抽象方法"""
        from ai.components.datasource.interfaces import BaseConnect
        import inspect

        # 获取所有抽象方法
        abstract_methods = [
            name for name, method in inspect.getmembers(BaseConnect)
            if getattr(method, '__isabstractmethod__', False)
        ]

        # 验证关键方法存在
        expected_methods = [
            'get_show_create_table',
            'get_example_data',
            'get_table_names',
            'get_table_info',
            'run',
        ]

        for method in expected_methods:
            assert method in abstract_methods, f"缺少抽象方法: {method}"
