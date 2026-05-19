"""Settings Loading Tests"""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import Field

from demo.configs.base import BaseSettings
from demo.configs.settings import Settings, ServerSettings, SqlalchemySettings


class TestSettingsLoad:
    """Settings loading tests"""

    def test_default_settings_load(self):
        """Test loading settings with default values"""
        settings = Settings()

        assert settings.name == "demo"
        assert settings.server.host == "0.0.0.0"
        assert settings.server.port == 8000

    def test_server_settings_defaults(self):
        """Test ServerSettings default values"""
        settings = ServerSettings()

        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.debug is False

    def test_sqlalchemy_settings_defaults(self):
        """Test SqlalchemySettings default values"""
        settings = SqlalchemySettings()

        assert "postgresql" in settings.database_url
        assert settings.echo is False
        assert settings.pool_size == 5

    def test_settings_from_dict(self):
        """Test creating settings from dictionary"""
        config = {
            "name": "test_app",
            "server": {
                "host": "127.0.0.1",
                "port": 9000,
                "debug": True
            }
        }

        settings = Settings.from_dict(config)

        assert settings.name == "test_app"
        assert settings.server.host == "127.0.0.1"
        assert settings.server.port == 9000
        assert settings.server.debug is True

    def test_nested_settings(self):
        """Test nested settings configuration"""
        config = {
            "server": {
                "port": 8080
            },
            "sqlalchemy": {
                "pool_size": 10
            }
        }

        settings = Settings.from_dict(config)

        assert settings.server.port == 8080
        assert settings.sqlalchemy.pool_size == 10


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

    def test_base_settings_to_dict(self):
        """Test BaseSettings.to_dict"""
        class TestSettings(BaseSettings):
            app_name: str = "test"

        settings = TestSettings()
        result = settings.to_dict()

        assert result["app_name"] == "test"
