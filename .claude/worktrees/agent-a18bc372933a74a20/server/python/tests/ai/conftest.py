# AI 模块测试公共 fixtures

import pytest


@pytest.fixture
def credential_schema():
    """标准凭证架构 fixture
    
    提供一个标准的凭证架构定义，包含敏感字段和非敏感字段。
    """
    return [
        {
            "name": "api_key",
            "type": "secret-input",
            "required": True,
            "label": "API Key",
        },
        {
            "name": "api_secret",
            "type": "secret",
            "required": True,
            "label": "API Secret",
        },
        {
            "name": "endpoint",
            "type": "text-input",
            "required": False,
            "label": "Endpoint URL",
        },
        {
            "name": "model_type",
            "type": "select",
            "required": True,
            "options": [
                {"label": "GPT-4", "value": "gpt-4"},
                {"label": "GPT-3.5", "value": "gpt-3.5"},
            ],
        },
    ]


@pytest.fixture
def sample_plugin_config():
    """示例插件配置 fixture
    
    提供一个完整的插件配置示例，包含工具配置和凭证架构。
    """
    return {
        "version": "1.0.0",
        "type": "plugin",
        "name": "test-plugin",
        "tools_configuration": [
            {
                "provider": "test_provider",
                "credentials_schema": [
                    {
                        "name": "api_key",
                        "type": "secret-input",
                        "required": True,
                        "label": "API Key",
                    },
                ],
            }
        ],
    }


@pytest.fixture
def sample_credentials():
    """示例凭证数据 fixture"""
    return {
        "api_key": "sk-test-api-key-12345",
        "api_secret": "secret-value-67890",
        "endpoint": "https://api.example.com",
        "model_type": "gpt-4",
    }
