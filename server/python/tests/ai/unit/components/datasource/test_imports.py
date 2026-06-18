"""
Datasource 组件导入测试

验证数据源组件的模块可以正确导入。

测试覆盖：
- interfaces 模块：BaseConnect 抽象基类
- base 模块：DbInfo、DBType 枚举
- rdbms.base 模块：RDBMSDatabase 基类
- rdbms.conn_mysql 模块：MySQLConnect 连接器
"""

import ast
from pathlib import Path

import pytest


class TestDatasourceImports:
    """Datasource 组件导入测试"""

    def test_import_interfaces_module(self):
        """测试导入 interfaces 模块"""
        from ai.components.datasource.interfaces import BaseConnect

        # 验证 BaseConnect 是抽象基类
        assert hasattr(BaseConnect, "__abstractmethods__")
        # 验证关键抽象方法存在
        assert hasattr(BaseConnect, "get_table_names")
        assert hasattr(BaseConnect, "run")
        assert hasattr(BaseConnect, "run_to_df")

    def test_import_base_module(self):
        """测试导入 base 模块"""
        from ai.components.datasource.base import DbInfo, DBType

        # 验证 DbInfo 可以实例化
        db_info = DbInfo("mysql")
        assert db_info.name == "mysql"
        assert db_info.is_file_db is False

        # 验证 DBType 枚举值
        assert DBType.MYSQL.value() == "mysql"
        assert DBType.POSTGRESQL.value() == "postgresql"
        assert DBType.SQLITE.is_file_db() is True

    def test_import_rdbms_base(self):
        """测试导入 rdbms.base 模块"""
        from ai.components.datasource.rdbms.base import RDBMSDatabase

        # 验证 RDBMSDatabase 是类
        assert isinstance(RDBMSDatabase, type)

    def test_import_mysql_connect(self):
        """测试导入 MySQL 连接器"""
        from ai.components.datasource.rdbms.conn_mysql import MySQLConnect

        # 验证 MySQLConnect 是类
        assert isinstance(MySQLConnect, type)

    def test_import_from_rdbms_package(self):
        """测试从 rdbms 包导入"""
        from ai.components.datasource.rdbms import MySQLConnect, RDBMSDatabase

        # 验证导出的类
        assert isinstance(RDBMSDatabase, type)
        assert isinstance(MySQLConnect, type)


class TestDatasourceSyntax:
    """Datasource 语法验证测试"""

    def test_all_python_files_have_valid_syntax(self):
        """验证所有 Python 文件语法有效"""
        datasource_dir = Path("src/ai/components/datasource")
        syntax_errors = []

        for py_file in datasource_dir.rglob("*.py"):
            try:
                with open(py_file, encoding="utf-8") as f:
                    source = f.read()
                ast.parse(source)
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}: {e}")

        assert not syntax_errors, f"发现语法错误:\n" + "\n".join(syntax_errors)

    def test_no_relative_imports_outside_package(self):
        """验证没有使用超出包范围的相对导入"""
        datasource_dir = Path("src/ai/components/datasource")
        invalid_imports = []

        for py_file in datasource_dir.rglob("*.py"):
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            # 检查是否有导入 ai.components 中其他组件的内容
            # 这些应该通过绝对导入处理
            if "from ... import" in content:
                invalid_imports.append(f"{py_file}: 发现超出包范围的相对导入")

        assert not invalid_imports, f"发现无效导入:\n" + "\n".join(invalid_imports)
