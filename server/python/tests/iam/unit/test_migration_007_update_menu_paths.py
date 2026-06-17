"""
迁移脚本测试：007_update_menu_paths_to_resources

测试菜单路径从 /admin/resource-configs 更新为 /admin/resources 的迁移脚本。
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib.util

# 动态导入迁移脚本（文件名以数字开头）
migration_path = (
    Path(__file__).parent.parent.parent.parent
    / "src" / "iam" / "migrations" / "versions"
    / "007_update_menu_paths_to_resources.py"
)

spec = importlib.util.spec_from_file_location(
    "migration_007",
    migration_path
)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)

# 提取迁移函数和元数据
upgrade = migration.upgrade
downgrade = migration.downgrade
revision = migration.revision
down_revision = migration.down_revision


class TestMigrationMetadata:
    """迁移元数据测试"""

    def test_revision_id(self):
        """测试迁移版本 ID 正确"""
        assert revision == "007_update_menu_paths_to_resources"

    def test_down_revision(self):
        """测试前置版本 ID 正确"""
        assert down_revision == "006_update_menu_paths"

    def test_upgrade_function_exists(self):
        """测试 upgrade 函数存在"""
        assert callable(upgrade)

    def test_downgrade_function_exists(self):
        """测试 downgrade 函数存在"""
        assert callable(downgrade)


class TestUpgrade:
    """upgrade 函数测试"""

    def test_upgrade_updates_tenant_module_menus(self):
        """测试 upgrade 更新 tenant.module_menus 表"""
        mock_op = MagicMock()

        with patch.object(migration, "op", mock_op):
            mock_op.execute.return_value = None
            upgrade()

        # 验证 op.execute 被调用两次（tenant.module_menus 和 iam.menus）
        assert mock_op.execute.call_count == 2

        # 获取调用的 SQL 语句
        calls = mock_op.execute.call_args_list
        sql_statements = [str(call[0][0]) for call in calls]

        # 验证 tenant.module_menus 更新语句
        tenant_update_found = any(
            "tenant.module_menus" in sql and "/admin/resources" in sql
            for sql in sql_statements
        )
        assert tenant_update_found, "应该包含更新 tenant.module_menus 的 SQL"

    def test_upgrade_updates_iam_menus(self):
        """测试 upgrade 更新 iam.menus 表"""
        mock_op = MagicMock()

        with patch.object(migration, "op", mock_op):
            mock_op.execute.return_value = None
            upgrade()

        calls = mock_op.execute.call_args_list
        sql_statements = [str(call[0][0]) for call in calls]

        # 验证 iam.menus 更新语句
        iam_update_found = any(
            "iam.menus" in sql and "/admin/resources" in sql
            for sql in sql_statements
        )
        assert iam_update_found, "应该包含更新 iam.menus 的 SQL"

    def test_upgrade_changes_path_from_resource_configs_to_resources(self):
        """测试 upgrade 将路径从 /admin/resource-configs 改为 /admin/resources"""
        mock_op = MagicMock()

        with patch.object(migration, "op", mock_op):
            mock_op.execute.return_value = None
            upgrade()

        calls = mock_op.execute.call_args_list

        for call in calls:
            sql_text = str(call[0][0])
            # 验证 SQL 语句包含正确的路径更新
            if "UPDATE" in sql_text.upper():
                assert "/admin/resources" in sql_text, "新路径应为 /admin/resources"
                assert "/admin/resource-configs" in sql_text, "旧路径应为 /admin/resource-configs"

    def test_upgrade_targets_tenant_resources_code(self):
        """测试 upgrade 只更新 code = 'tenant.resources' 的菜单"""
        mock_op = MagicMock()

        with patch.object(migration, "op", mock_op):
            mock_op.execute.return_value = None
            upgrade()

        calls = mock_op.execute.call_args_list

        for call in calls:
            sql_text = str(call[0][0])
            if "UPDATE" in sql_text.upper():
                assert "tenant.resources" in sql_text, "应该只更新 code = 'tenant.resources' 的菜单"


class TestDowngrade:
    """downgrade 函数测试"""

    def test_downgrade_reverts_tenant_module_menus(self):
        """测试 downgrade 回滚 tenant.module_menus 表"""
        mock_op = MagicMock()

        with patch.object(migration, "op", mock_op):
            mock_op.execute.return_value = None
            downgrade()

        assert mock_op.execute.call_count == 2

        calls = mock_op.execute.call_args_list
        sql_statements = [str(call[0][0]) for call in calls]

        # 验证回滚语句存在
        tenant_rollback_found = any(
            "tenant.module_menus" in sql and "/admin/resource-configs" in sql
            for sql in sql_statements
        )
        assert tenant_rollback_found, "应该包含回滚 tenant.module_menus 的 SQL"

    def test_downgrade_reverts_iam_menus(self):
        """测试 downgrade 回滚 iam.menus 表"""
        mock_op = MagicMock()

        with patch.object(migration, "op", mock_op):
            mock_op.execute.return_value = None
            downgrade()

        calls = mock_op.execute.call_args_list
        sql_statements = [str(call[0][0]) for call in calls]

        iam_rollback_found = any(
            "iam.menus" in sql and "/admin/resource-configs" in sql
            for sql in sql_statements
        )
        assert iam_rollback_found, "应该包含回滚 iam.menus 的 SQL"

    def test_downgrade_changes_path_from_resources_to_resource_configs(self):
        """测试 downgrade 将路径从 /admin/resources 改回 /admin/resource-configs"""
        mock_op = MagicMock()

        with patch.object(migration, "op", mock_op):
            mock_op.execute.return_value = None
            downgrade()

        calls = mock_op.execute.call_args_list

        for call in calls:
            sql_text = str(call[0][0])
            if "UPDATE" in sql_text.upper():
                # 回滚时：新路径 -> 旧路径
                assert "/admin/resource-configs" in sql_text, "回滚后路径应为 /admin/resource-configs"
                assert "/admin/resources" in sql_text, "回滚前路径应为 /admin/resources"

    def test_downgrade_targets_tenant_resources_code(self):
        """测试 downgrade 只更新 code = 'tenant.resources' 的菜单"""
        mock_op = MagicMock()

        with patch.object(migration, "op", mock_op):
            mock_op.execute.return_value = None
            downgrade()

        calls = mock_op.execute.call_args_list

        for call in calls:
            sql_text = str(call[0][0])
            if "UPDATE" in sql_text.upper():
                assert "tenant.resources" in sql_text, "应该只更新 code = 'tenant.resources' 的菜单"


class TestUpgradeDowngradeSymmetry:
    """upgrade 和 downgrade 对称性测试"""

    def test_upgrade_and_downgrade_are_inverse_operations(self):
        """测试 upgrade 和 downgrade 是互逆操作"""
        mock_op = MagicMock()

        # 执行 upgrade
        with patch.object(migration, "op", mock_op):
            mock_op.execute.return_value = None
            upgrade()
            upgrade_calls = list(mock_op.execute.call_args_list)

        # 重置 mock
        mock_op.reset_mock()

        # 执行 downgrade
        with patch.object(migration, "op", mock_op):
            mock_op.execute.return_value = None
            downgrade()
            downgrade_calls = list(mock_op.execute.call_args_list)

        # 验证调用次数相同
        assert len(upgrade_calls) == len(downgrade_calls), "upgrade 和 downgrade 应该有相同数量的 SQL 语句"

        # 验证操作的表相同
        upgrade_tables = set()
        downgrade_tables = set()

        for call in upgrade_calls:
            sql = str(call[0][0])
            if "tenant.module_menus" in sql:
                upgrade_tables.add("tenant.module_menus")
            if "iam.menus" in sql:
                upgrade_tables.add("iam.menus")

        for call in downgrade_calls:
            sql = str(call[0][0])
            if "tenant.module_menus" in sql:
                downgrade_tables.add("tenant.module_menus")
            if "iam.menus" in sql:
                downgrade_tables.add("iam.menus")

        assert upgrade_tables == downgrade_tables, "upgrade 和 downgrade 应该操作相同的表"
