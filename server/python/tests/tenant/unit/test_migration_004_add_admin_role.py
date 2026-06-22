"""
迁移脚本测试：004_add_admin_role

测试 tenant_admins 表新增 role 字段的迁移脚本。
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import importlib.util

# 动态导入迁移脚本
_migration_path = (
    Path(__file__).parent.parent.parent.parent
    / "src" / "tenant" / "migrations" / "versions"
    / "004_add_admin_role.py"
)

spec = importlib.util.spec_from_file_location(
    "migration_004",
    _migration_path,
)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)

# 提取迁移函数和元数据
upgrade = migration.upgrade
downgrade = migration.downgrade
revision = migration.revision
down_revision = migration.down_revision
MODULE_SCHEMA = migration.MODULE_SCHEMA


class TestMigrationMetadata:
    """迁移元数据测试"""

    def test_revision_id(self):
        """测试迁移版本 ID 正确"""
        assert revision == "004_add_admin_role"

    def test_down_revision(self):
        """测试前置版本 ID 正确"""
        assert down_revision == "003_module_menu_tree_fields"

    def test_upgrade_function_exists(self):
        """测试 upgrade 函数存在"""
        assert callable(upgrade)

    def test_downgrade_function_exists(self):
        """测试 downgrade 函数存在"""
        assert callable(downgrade)

    def test_module_schema_is_tenant(self):
        """测试模块 schema 为 tenant"""
        assert MODULE_SCHEMA == "tenant"


class TestUpgrade:
    """upgrade 函数测试"""

    def test_upgrade_adds_role_column(self):
        """测试 upgrade 添加 role 列到 tenant_admins 表"""
        mock_op = MagicMock()

        with patch.object(migration, "op", mock_op):
            upgrade()

        # 验证 op.add_column 被调用
        assert mock_op.add_column.call_count == 1

        # 获取 add_column 调用的参数
        call_args = mock_op.add_column.call_args
        table_name = call_args[0][0]
        column = call_args[0][1]
        schema = call_args[1]["schema"]

        assert table_name == "tenant_admins"
        assert schema == MODULE_SCHEMA

        # 验证列定义
        from sqlalchemy import String
        assert isinstance(column.type, String)
        assert column.type.length == 50
        assert column.nullable is False
        assert column.server_default.arg == "ordinaryAdmin"
        assert column.comment == "角色编码"


class TestDowngrade:
    """downgrade 函数测试"""

    def test_downgrade_drops_role_column(self):
        """测试 downgrade 删除 tenant_admins 表的 role 列"""
        mock_op = MagicMock()

        with patch.object(migration, "op", mock_op):
            downgrade()

        # 验证 op.drop_column 被调用
        mock_op.drop_column.assert_called_once_with(
            "tenant_admins",
            "role",
            schema=MODULE_SCHEMA,
        )


class TestUpgradeDowngradeSymmetry:
    """upgrade 和 downgrade 对称性测试"""

    def test_upgrade_and_downgrade_are_inverse(self):
        """测试 upgrade 和 downgrade 操作相同表"""
        mock_op = MagicMock()

        # 执行 upgrade
        with patch.object(migration, "op", mock_op):
            mock_op.add_column.return_value = None
            upgrade()

        # 重置 mock
        mock_op.reset_mock()

        # 执行 downgrade
        with patch.object(migration, "op", mock_op):
            mock_op.drop_column.return_value = None
            downgrade()

        # downgrade 应该操作同一张表
        mock_op.drop_column.assert_called_once()
        table_name = mock_op.drop_column.call_args[0][0]
        assert table_name == "tenant_admins"
