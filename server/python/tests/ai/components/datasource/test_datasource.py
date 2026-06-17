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
