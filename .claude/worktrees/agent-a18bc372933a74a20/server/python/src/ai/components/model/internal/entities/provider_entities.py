"""
提供者相关实体类

迁移自 Alon: src/alon/components/model/internal/entities/provider_entities.py
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ai_plugin.sdk.entities.model import ModelType


class ModelSettings(BaseModel):
    """模型设置"""

    model: str
    model_type: Any  # ModelType
    enabled: bool


class CustomProviderConfiguration(BaseModel):
    """自定义提供者配置"""

    credentials: dict[str, Any]


class CustomModelConfiguration(BaseModel):
    """
    Model class for provider custom model configuration.
    """

    model: str
    model_type: ModelType
    credentials: dict

    # pydantic configs
    model_config = ConfigDict(protected_namespaces=())


class CustomConfiguration(BaseModel):
    """自定义配置"""

    provider: CustomProviderConfiguration | None = None
    models: list[CustomModelConfiguration] = []


class SimpleProviderConfig(BaseModel):
    """简化的提供者配置"""

    provider: str
    credentials: dict[str, Any] = Field(default_factory=dict)
