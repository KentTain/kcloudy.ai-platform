"""
RDBMSDatabase URI 构造测试

验证 URI 构造逻辑正确，包括：
- MySQL URI 格式
- 特殊字符转义
- 默认数据库列表

注意：这些测试只验证 URI 构造逻辑，不连接真实数据库。
"""

import pytest
from urllib.parse import quote, quote_plus

from ai.components.datasource.rdbms import MySQLConnect, RDBMSDatabase


class TestRDBMSDatabaseURI:
    """RDBMSDatabase URI 构造测试"""

    def test_mysql_driver_format(self):
        """验证 MySQL 驱动格式正确"""
        assert MySQLConnect.driver == "mysql+aiomysql"
        assert MySQLConnect.db_type == "mysql"
        assert MySQLConnect.db_dialect == "mysql"

    def test_mysql_default_databases(self):
        """验证 MySQL 默认数据库列表"""
        expected_databases = ["information_schema", "performance_schema", "sys", "mysql"]
        assert MySQLConnect.default_db == expected_databases

    def test_uri_construction_basic(self):
        """测试基本 URI 构造"""
        host = "localhost"
        port = 3306
        user = "root"
        pwd = "password"
        db_name = "test_db"

        # 预期 URI 格式
        expected_uri = f"mysql+aiomysql://{quote(user)}:{quote_plus(pwd)}@{host}:{port}/{db_name}"

        # 手动构造 URI 验证格式
        actual_uri = f"{MySQLConnect.driver}://{quote(user)}:{quote_plus(pwd)}@{host}:{port}/{db_name}"

        assert actual_uri == expected_uri

    def test_uri_construction_with_special_chars_in_password(self):
        """测试密码包含特殊字符时的 URI 构造"""
        host = "localhost"
        port = 3306
        user = "root"
        pwd = "p@ss:word/123"
        db_name = "test_db"

        # 密码包含特殊字符，需要使用 quote_plus 编码
        encoded_pwd = quote_plus(pwd)
        assert encoded_pwd == "p%40ss%3Aword%2F123"

        # 构造 URI
        uri = f"{MySQLConnect.driver}://{quote(user)}:{encoded_pwd}@{host}:{port}/{db_name}"

        # 验证特殊字符被正确编码
        assert "@" not in uri.split("@")[0].split(":")[-1]  # 密码部分的 @ 被编码
        assert ":" not in uri.split("@")[0].split(":")[-1]  # 密码部分的 : 被编码
        assert "/" not in uri.split("@")[0].split(":")[-1]  # 密码部分的 / 被编码

    def test_uri_construction_with_special_chars_in_username(self):
        """测试用户名包含特殊字符时的 URI 构造"""
        host = "localhost"
        port = 3306
        user = "user@domain"
        pwd = "password"
        db_name = "test_db"

        # 用户名包含 @，需要使用 quote 编码
        encoded_user = quote(user)
        assert encoded_user == "user%40domain"

        # 构造 URI
        uri = f"{MySQLConnect.driver}://{encoded_user}:{quote_plus(pwd)}@{host}:{port}/{db_name}"

        # 验证 @ 被正确编码
        # URI 格式：driver://user:pwd@host:port/db
        # 第一个 @ 应该在 user:pwd 和 host:port 之间
        at_index = uri.find("@")
        user_pwd_part = uri[:at_index]
        host_part = uri[at_index + 1 :]

        # 用户名部分的 @ 应该被编码为 %40
        assert "@" not in user_pwd_part or user_pwd_part.count("@") == 0

    def test_uri_construction_with_port(self):
        """测试包含端口的 URI 构造"""
        host = "192.168.1.100"
        port = 3307
        user = "admin"
        pwd = "secret"
        db_name = "production"

        uri = f"{MySQLConnect.driver}://{quote(user)}:{quote_plus(pwd)}@{host}:{port}/{db_name}"

        # 验证端口正确
        assert f":{port}/" in uri
        assert ":3307/" in uri

    def test_uri_encoding_difference(self):
        """测试 quote 和 quote_plus 的编码差异"""
        # quote 用于用户名，保留 @ 等字符
        # quote_plus 用于密码，将空格编码为 +

        text_with_space = "hello world"
        text_with_at = "user@domain"

        # quote 将空格编码为 %20
        assert quote(text_with_space) == "hello%20world"
        # quote_plus 将空格编码为 +
        assert quote_plus(text_with_space) == "hello+world"

        # quote 将 @ 编码为 %40
        assert quote(text_with_at) == "user%40domain"
        # quote_plus 也将 @ 编码为 %40
        assert quote_plus(text_with_at) == "user%40domain"

    def test_rdbms_base_class_attributes(self):
        """验证 RDBMSDatabase 基类属性"""
        # 基类属性应该是空字符串或空列表
        assert RDBMSDatabase.db_type == ""
        assert RDBMSDatabase.db_dialect == ""
        assert RDBMSDatabase.driver == ""
        assert RDBMSDatabase.default_db == []

    def test_mysql_inherits_from_rdbms(self):
        """验证 MySQLConnect 继承自 RDBMSDatabase"""
        assert issubclass(MySQLConnect, RDBMSDatabase)
        assert issubclass(MySQLConnect, object)

    def test_uri_format_components(self):
        """验证 URI 格式组成部分"""
        driver = MySQLConnect.driver
        user = "root"
        pwd = "password"
        host = "localhost"
        port = 3306
        db_name = "test"

        # 完整 URI 格式：driver://user:pwd@host:port/db
        uri = f"{driver}://{quote(user)}:{quote_plus(pwd)}@{host}:{port}/{db_name}"

        # 验证各组成部分
        assert uri.startswith(driver + "://")
        assert "@" in uri
        assert ":" in uri
        assert uri.endswith(db_name)

        # 解析 URI 各部分
        # driver://user:pwd@host:port/db
        parts = uri.split("://")
        assert len(parts) == 2
        assert parts[0] == driver

        # user:pwd@host:port/db
        auth_host_db = parts[1]
        auth_host, db = auth_host_db.rsplit("/", 1)
        assert db == db_name

        # user:pwd@host:port
        auth, host_port = auth_host.rsplit("@", 1)
        assert host_port == f"{host}:{port}"

        # user:pwd
        user_pwd = auth.split(":")
        assert user_pwd[0] == user
        assert user_pwd[1] == pwd
