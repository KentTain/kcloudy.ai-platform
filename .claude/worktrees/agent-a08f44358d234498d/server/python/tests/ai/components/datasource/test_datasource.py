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


class TestRDBMSDatabaseURI:
    """RDBMSDatabase URI 构造测试"""

    def test_uri_construction_mysql(self):
        """测试 MySQL URI 格式生成"""
        from ai.components.datasource.rdbms.conn_mysql import MySQLConnect

        # 验证 MySQL URI 格式
        expected_driver = "mysql+aiomysql"
        assert MySQLConnect.driver == expected_driver

        # 验证默认数据库列表
        assert "information_schema" in MySQLConnect.default_db
        assert "performance_schema" in MySQLConnect.default_db

    def test_uri_with_special_characters(self):
        """测试特殊字符转义"""
        from urllib.parse import quote, quote_plus

        # 测试用户名包含特殊字符
        user = "user@domain"
        encoded_user = quote(user)
        assert encoded_user == "user%40domain"

        # 测试密码包含特殊字符
        pwd = "p@ss:word/123"
        encoded_pwd = quote_plus(pwd)
        assert encoded_pwd == "p%40ss%3Aword%2F123"

    def test_default_database_list(self):
        """测试默认数据库列表"""
        from ai.components.datasource.rdbms.conn_mysql import MySQLConnect

        expected_dbs = ["information_schema", "performance_schema", "sys", "mysql"]
        assert MySQLConnect.default_db == expected_dbs


class TestSQLParsing:
    """SQL 解析功能测试"""

    def test_sqlparse_format(self):
        """测试 SQL 格式化"""
        import sqlparse

        sql = "select * from users where id=1"
        formatted = sqlparse.format(sql, reindent=True, keyword_case='upper')

        # 验证关键字被大写
        assert "SELECT" in formatted
        assert "FROM" in formatted
        assert "WHERE" in formatted

    def test_sqlparse_split(self):
        """测试 SQL 拆分"""
        import sqlparse

        sql = "SELECT * FROM users; INSERT INTO users VALUES (1);"
        statements = sqlparse.split(sql)

        # 验证拆分为多条语句
        assert len(statements) == 2
        assert "SELECT" in statements[0]
        assert "INSERT" in statements[1]

    def test_regex_patterns(self):
        """测试正则表达式功能"""
        import regex

        # 测试基本正则匹配
        pattern = r'\b\w+@\w+\.\w+\b'
        text = "联系邮箱: test@example.com 和 admin@site.org"
        matches = regex.findall(pattern, text)

        assert len(matches) == 2
        assert "test@example.com" in matches
        assert "admin@site.org" in matches

        # 测试 Unicode 支持
        chinese_pattern = r'[\p{Han}]+'
        chinese_text = "这是中文测试"
        chinese_matches = regex.findall(chinese_pattern, chinese_text)

        assert len(chinese_matches) > 0
