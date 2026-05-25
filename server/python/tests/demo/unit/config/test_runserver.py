"""Runserver command tests"""

from alembic.script import ScriptDirectory
from click.testing import CliRunner

from manage import cli, get_alembic_config


class TestRunserverCommand:
    """Runserver command tests"""

    def test_prints_loopback_url_when_binding_all_interfaces(self, mocker):
        """Test runserver prints a browsable URL for 0.0.0.0 bind address"""
        uvicorn_run = mocker.patch("uvicorn.run")

        result = CliRunner().invoke(cli, ["runserver", "--host", "0.0.0.0", "--port", "8081"])

        assert result.exit_code == 0
        assert "地址: http://127.0.0.1:8081" in result.output
        assert "文档: http://127.0.0.1:8081/docs" in result.output
        uvicorn_run.assert_called_once()


class TestMigrateCommand:
    """Migrate 命令测试"""

    def test_migrate_defaults_to_heads(self):
        """
        场景：存在多个迁移 head
        WHEN: 查看 migrate 命令的 revision 默认值
        THEN: 默认值为 heads
        """
        db_group = cli.commands["db"]  # type: ignore[index]
        migrate_cmd = db_group.commands["migrate"]  # type: ignore[index]
        revision_param = next(p for p in migrate_cmd.params if p.name == "revision")
        assert revision_param.default == "heads"


class TestAlembicConfig:
    """Alembic 配置测试"""

    def test_alembic_config_includes_iam_migrations(self):
        """
        场景：检查迁移配置
        WHEN: 加载 Alembic 配置
        THEN: 同时包含 demo 和 iam 两个迁移目录
        """
        config = get_alembic_config()

        version_locations = config.get_main_option("version_locations")
        assert version_locations is not None, "version_locations 未配置"

        normalized_locations = version_locations.replace("\\", "/")
        assert "src/demo/migrations/versions" in normalized_locations
        assert "src/iam/migrations/versions" in normalized_locations

        revisions = {revision.revision for revision in ScriptDirectory.from_config(config).walk_revisions()}
        assert "001_tenant" in revisions
        assert "demo_002_tenant_dataset" in revisions
        assert "demo_001_create_dataset" in revisions