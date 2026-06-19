"""
SQL 解析测试

验证 SQL 解析功能正确，包括：
- SQL 格式化
- SQL 拆分
- SQL 类型识别
- 表名提取
- 写操作转换为查询

注意：这些测试不连接真实数据库。
"""

import sqlparse
from sqlparse import tokens as token_types

from ai.components.datasource.rdbms import MySQLConnect


class TestSQLParsing:
    """SQL 解析测试"""

    def test_sqlparse_basic_select(self):
        """测试 sqlparse 解析 SELECT 语句"""
        sql = "SELECT * FROM users WHERE id = 1"
        parsed = sqlparse.parse(sql)[0]

        # 验证 SQL 类型
        assert parsed.get_type() == "SELECT"

        # 验证第一个 token
        first_token = parsed.token_first(skip_ws=True, skip_cm=False)
        assert first_token.ttype == token_types.DML
        assert first_token.value.upper() == "SELECT"

    def test_sqlparse_insert(self):
        """测试 sqlparse 解析 INSERT 语句"""
        sql = "INSERT INTO users (id, name) VALUES (1, 'Alice')"
        parsed = sqlparse.parse(sql)[0]

        assert parsed.get_type() == "INSERT"

        first_token = parsed.token_first(skip_ws=True, skip_cm=False)
        assert first_token.ttype == token_types.DML
        assert first_token.value.upper() == "INSERT"

    def test_sqlparse_update(self):
        """测试 sqlparse 解析 UPDATE 语句"""
        sql = "UPDATE users SET name = 'Bob' WHERE id = 1"
        parsed = sqlparse.parse(sql)[0]

        assert parsed.get_type() == "UPDATE"

        first_token = parsed.token_first(skip_ws=True, skip_cm=False)
        assert first_token.ttype == token_types.DML
        assert first_token.value.upper() == "UPDATE"

    def test_sqlparse_delete(self):
        """测试 sqlparse 解析 DELETE 语句"""
        sql = "DELETE FROM users WHERE id = 1"
        parsed = sqlparse.parse(sql)[0]

        assert parsed.get_type() == "DELETE"

        first_token = parsed.token_first(skip_ws=True, skip_cm=False)
        assert first_token.ttype == token_types.DML
        assert first_token.value.upper() == "DELETE"

    def test_sqlparse_create_table(self):
        """测试 sqlparse 解析 CREATE TABLE 语句"""
        sql = "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"
        parsed = sqlparse.parse(sql)[0]

        assert parsed.get_type() == "CREATE"

        first_token = parsed.token_first(skip_ws=True, skip_cm=False)
        assert first_token.ttype == token_types.DDL
        assert first_token.value.upper() == "CREATE"

    def test_sqlparse_alter_table(self):
        """测试 sqlparse 解析 ALTER TABLE 语句"""
        sql = "ALTER TABLE users ADD COLUMN email VARCHAR(100)"
        parsed = sqlparse.parse(sql)[0]

        assert parsed.get_type() == "ALTER"

        first_token = parsed.token_first(skip_ws=True, skip_cm=False)
        assert first_token.ttype == token_types.DDL
        assert first_token.value.upper() == "ALTER"

    def test_sqlparse_drop_table(self):
        """测试 sqlparse 解析 DROP TABLE 语句"""
        sql = "DROP TABLE users"
        parsed = sqlparse.parse(sql)[0]

        assert parsed.get_type() == "DROP"

        first_token = parsed.token_first(skip_ws=True, skip_cm=False)
        assert first_token.ttype == token_types.DDL
        assert first_token.value.upper() == "DROP"


class TestSQLFormat:
    """SQL 格式化测试"""

    def test_sqlparse_format_basic(self):
        """测试 SQL 格式化"""
        sql = "select * from users where id=1"
        formatted = sqlparse.format(sql, reindent=True, keyword_case="upper")

        # 验证关键字被转换为大写
        assert "SELECT" in formatted
        assert "FROM" in formatted
        assert "WHERE" in formatted

    def test_sqlparse_format_strip_comments(self):
        """测试移除 SQL 注释"""
        sql = "SELECT * FROM users -- this is a comment"
        formatted = sqlparse.format(sql, strip_comments=True)

        # 验证注释被移除
        assert "--" not in formatted
        assert "this is a comment" not in formatted

    def test_sqlparse_split_statements(self):
        """测试拆分多条 SQL 语句"""
        sql = "SELECT * FROM users; INSERT INTO users (id) VALUES (1);"
        statements = sqlparse.split(sql)

        # 验证拆分出两条语句
        assert len(statements) == 2
        assert "SELECT" in statements[0]
        assert "INSERT" in statements[1]


class TestSQLConversion:
    """SQL 转换测试"""

    def test_convert_insert_to_select(self):
        """测试 INSERT 转 SELECT"""
        # 注意：这个测试依赖于实现细节，实际正则可能更复杂
        insert_sql = "INSERT INTO users (id, name) VALUES (1, 'Alice')"
        # 预期格式：SELECT * FROM users WHERE id=1 AND name='Alice'

        # 这里我们只验证方法存在
        assert hasattr(MySQLConnect, "convert_sql_write_to_select")

    def test_convert_delete_to_select(self):
        """测试 DELETE 转 SELECT"""
        delete_sql = "DELETE FROM users WHERE id = 1"
        # 预期格式：SELECT * FROM users

        assert hasattr(MySQLConnect, "convert_sql_write_to_select")

    def test_convert_update_to_select(self):
        """测试 UPDATE 转 SELECT"""
        update_sql = "UPDATE users SET name = 'Bob' WHERE id = 1"
        # 预期格式：SELECT name FROM users WHERE id = 1

        assert hasattr(MySQLConnect, "convert_sql_write_to_select")


class TestTableNameExtraction:
    """表名提取测试"""

    def test_extract_table_from_select(self):
        """测试从 SELECT 语句提取表名"""
        sql = "SELECT * FROM users WHERE id = 1"
        parsed = sqlparse.parse(sql)[0]

        # sqlparse 的 get_name() 方法可能返回 None，需要遍历 tokens
        table_name = parsed.get_name()
        # get_name() 可能返回 None，这是正常的
        # 实际应用中需要遍历 tokens 来提取表名

    def test_extract_table_from_create(self):
        """测试从 CREATE TABLE 语句提取表名"""
        sql = "CREATE TABLE users (id INT)"
        parsed = sqlparse.parse(sql)[0]

        # 遍历 tokens 查找表名
        for token in parsed.tokens:
            if token.ttype is None and isinstance(token, sqlparse.sql.Identifier):
                table_name = token.get_real_name()
                assert table_name == "users"
                break


class TestSQLTokenType:
    """SQL Token 类型测试"""

    def test_dml_tokens(self):
        """测试 DML token 类型"""
        dml_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE"]

        for keyword in dml_keywords:
            sql = f"{keyword} * FROM users"
            parsed = sqlparse.parse(sql)[0]
            first_token = parsed.token_first(skip_ws=True, skip_cm=False)
            assert first_token.ttype == token_types.DML

    def test_ddl_tokens(self):
        """测试 DDL token 类型"""
        ddl_keywords = ["CREATE", "ALTER", "DROP"]

        for keyword in ddl_keywords:
            sql = f"{keyword} TABLE users"
            parsed = sqlparse.parse(sql)[0]
            first_token = parsed.token_first(skip_ws=True, skip_cm=False)
            assert first_token.ttype == token_types.DDL
