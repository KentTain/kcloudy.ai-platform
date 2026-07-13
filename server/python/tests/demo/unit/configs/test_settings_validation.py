"""Settings Validation Tests"""

import pytest
from pydantic import Field, ValidationError, field_validator

from demo.configs import BaseSettings


class TestSettingsValidation:

    def test_valid_port_number(self):
        class ServerSettings(BaseSettings):
            port: int = Field(ge=1, le=65535)
        settings = ServerSettings(port=8080)
        assert settings.port == 8080

    def test_invalid_port_too_low(self):
        class ServerSettings(BaseSettings):
            port: int = Field(ge=1, le=65535)
        with pytest.raises(ValidationError):
            ServerSettings(port=0)

    def test_invalid_port_too_high(self):
        class ServerSettings(BaseSettings):
            port: int = Field(ge=1, le=65535)
        with pytest.raises(ValidationError):
            ServerSettings(port=70000)

    def test_custom_validator(self):
        class Settings(BaseSettings):
            name: str
            @field_validator('name')
            @classmethod
            def validate_name(cls, v):
                if len(v) < 3:
                    raise ValueError('Name must be at least 3 characters')
                return v
        settings = Settings(name='test')
        assert settings.name == 'test'
