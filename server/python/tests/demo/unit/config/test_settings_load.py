"""Settings Loading Tests"""

import importlib
import sys

from pydantic import Field

from framework.configs.base import BaseSettings
from framework.configs.settings import ServerSettings, Settings, SqlalchemySettings


class TestSettingsLoad:
    """Settings loading tests"""

    def test_default_settings_load(self):
        """Test loading settings with default values"""
        settings = Settings()

        assert settings.server.host == "0.0.0.0"
        assert settings.server.port == 8080

    def test_server_settings_defaults(self):
        """Test ServerSettings default values"""
        settings = ServerSettings()

        assert settings.host == "0.0.0.0"
        assert settings.port == 8080
        assert settings.workers == 1

    def test_sqlalchemy_settings_defaults(self):
        """Test SqlalchemySettings default values"""
        settings = SqlalchemySettings()

        assert settings.url == ""
        assert settings.echo is False
        assert settings.pool.size == 20

    def test_settings_from_dict(self):
        """Test creating settings from dictionary"""
        config = {
            "server": {
                "host": "127.0.0.1",
                "port": 9000,
            }
        }

        settings = Settings.from_dict(config)

        assert settings.server.host == "127.0.0.1"
        assert settings.server.port == 9000

    def test_nested_settings(self):
        """Test nested settings configuration"""
        config = {
            "server": {
                "port": 8080
            },
            "sqlalchemy": {
                "pool": {
                    "size": 10
                }
            }
        }

        settings = Settings.from_dict(config)

        assert settings.server.port == 8080
        assert settings.sqlalchemy.pool.size == 10
    def test_demo_settings_initializes_framework_global_settings(self):
        """Test demo settings initializes framework global settings"""
        import framework.configs.settings as framework_settings_module
        from framework.configs import get_settings

        framework_settings_module._settings = None
        sys.modules.pop("demo.configs", None)

        demo_configs = importlib.import_module("demo.configs")

        assert get_settings() is demo_configs.settings


class TestBaseSettings:
    """BaseSettings behavior tests"""

    def test_base_settings_creation(self):
        """Test creating BaseSettings subclass"""
        class TestSettings(BaseSettings):
            app_name: str = Field(default="test")
            debug: bool = Field(default=False)

        settings = TestSettings()

        assert settings.app_name == "test"
        assert settings.debug is False

    def test_base_settings_from_dict(self):
        """Test BaseSettings.from_dict"""
        class TestSettings(BaseSettings):
            app_name: str
            debug: bool

        settings = TestSettings.from_dict({
            "app_name": "custom",
            "debug": True
        })

        assert settings.app_name == "custom"
        assert settings.debug is True

    def test_base_settings_model_dump(self):
        """Test BaseSettings.model_dump"""
        class TestSettings(BaseSettings):
            app_name: str = "test"

        settings = TestSettings()
        result = settings.model_dump()

        assert result["app_name"] == "test"
