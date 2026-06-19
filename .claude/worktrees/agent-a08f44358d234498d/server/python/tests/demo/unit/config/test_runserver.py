"""Runserver command tests"""

from alembic.script import ScriptDirectory
from click.testing import CliRunner

from manage import cli


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

    def test_migrate_supports_module_option(self):
        """
        场景：模块化单体架构下，migrate 命令按模块独立迁移
        WHEN: 查看 migrate 命令的参数
        THEN: 支持 --module 和 --all 参数选择目标模块
        """
        db_group = cli.commands["db"]  # type: ignore[index]
        migrate_cmd = db_group.commands["migrate"]  # type: ignore[index]
        param_names = {p.name for p in migrate_cmd.params}
        assert "module" in param_names
        assert "all_modules" in param_names


class TestAlembicConfig:
    """Alembic 配置测试（模块化单体架构）"""

    def test_module_alembic_config_demo(self):
        """Demo 模块的 Alembic 配置应正确设置"""
        from manage import get_module_alembic_config, load_all_modules

        modules = load_all_modules()
        demo_module = next((m for m in modules if m.name == "demo"), None)
        assert demo_module is not None, "未找到 demo 模块"

        config = get_module_alembic_config(demo_module)
        assert config.get_main_option("script_location").replace("\\", "/").endswith("demo/migrations")
        assert "demo/migrations/versions" in config.get_main_option("version_locations").replace("\\", "/")

        revisions = {revision.revision for revision in ScriptDirectory.from_config(config).walk_revisions()}
        assert "001_demo" in revisions

    def test_module_alembic_config_iam(self):
        """IAM 模块的 Alembic 配置应正确设置"""
        from manage import get_module_alembic_config, load_all_modules

        modules = load_all_modules()
        iam_module = next((m for m in modules if m.name == "iam"), None)
        assert iam_module is not None, "未找到 iam 模块"

        config = get_module_alembic_config(iam_module)
        assert config.get_main_option("script_location").replace("\\", "/").endswith("iam/migrations")
        assert "iam/migrations/versions" in config.get_main_option("version_locations").replace("\\", "/")

        revisions = {revision.revision for revision in ScriptDirectory.from_config(config).walk_revisions()}
        assert "001_iam" in revisions
