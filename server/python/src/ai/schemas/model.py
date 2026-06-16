"""模型列表 Schema

定义模型列表接口的响应 Schema。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ai_plugin.sdk.entities import I18nObject
    from ai_plugin.sdk.entities.model import ProviderModel


class ModelItem(BaseModel):
    """模型项 Schema"""

    id: str = Field(description="模型 ID，格式为 provider/model")
    name: str = Field(description="模型名称")
    description: str | None = Field(default=None, description="模型描述")

    @classmethod
    def from_entity(cls, provider: str, model: "ProviderModel") -> "ModelItem":
        """从 ProviderModel 实体构建 ModelItem

        Args:
            provider: 提供商名称
            model: ProviderModel 实体对象

        Returns:
            ModelItem 实例
        """
        description = model.label.zh_Hans or model.label.en_US
        return cls(
            id=f"{provider}/{model.model}",
            name=model.model,
            description=description,
        )


class ProviderItem(BaseModel):
    """提供商项 Schema"""

    id: str = Field(description="提供商 ID")
    name: str = Field(description="提供商显示名称")
    models: list[ModelItem] = Field(default_factory=list, description="模型列表")

    @classmethod
    def from_entity(
        cls,
        provider_id: str,
        provider_label: "I18nObject",
        models: list["ProviderModel"],
    ) -> "ProviderItem":
        """从提供商实体构建 ProviderItem

        Args:
            provider_id: 提供商 ID
            provider_label: 提供商显示名称（I18nObject）
            models: 该提供商下的模型列表

        Returns:
            ProviderItem 实例
        """
        provider_name = provider_label.zh_Hans or provider_label.en_US
        model_items = [
            ModelItem.from_entity(provider_id, model)
            for model in models
        ]
        return cls(
            id=provider_id,
            name=provider_name,
            models=model_items,
        )


class ModelListResponse(BaseModel):
    """模型列表响应 Schema"""

    providers: list[ProviderItem] = Field(default_factory=list, description="提供商列表")
