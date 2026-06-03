from collections.abc import Sequence
from enum import Enum

from pydantic import BaseModel, ConfigDict

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.sdk.entities.model import ModelType, ProviderModel
from ai_plugin.sdk.entities.model.provider import ProviderEntity


class ModelStatus(Enum):
    """
    模型状态枚举类
    """

    ACTIVE = "active"
    NO_CONFIGURE = "no-configure"
    QUOTA_EXCEEDED = "quota-exceeded"
    NO_PERMISSION = "no-permission"
    DISABLED = "disabled"


class SimpleModelProviderEntity(BaseModel):
    """
    简单供应商实体类
    """

    provider: str
    label: I18nObject
    icon_small: I18nObject | None = None
    icon_large: I18nObject | None = None
    supported_model_types: list[ModelType]

    def __init__(self, provider_entity: ProviderEntity) -> None:
        """
        初始化简单供应商实体

        :param provider_entity: 供应商实体
        """
        super().__init__(
            provider=provider_entity.provider,
            label=provider_entity.label,
            icon_small=provider_entity.icon_small,
            icon_large=provider_entity.icon_large,
            supported_model_types=provider_entity.supported_model_types,
        )


class ProviderModelWithStatusEntity(ProviderModel):
    """
    带状态的供应商模型实体类
    """

    status: ModelStatus


class ModelWithProviderEntity(ProviderModelWithStatusEntity):
    """
    带供应商信息的模型实体类
    """

    provider: SimpleModelProviderEntity


class DefaultModelProviderEntity(BaseModel):
    """
    默认模型供应商实体类
    """

    provider: str
    label: I18nObject
    icon_small: I18nObject | None = None
    icon_large: I18nObject | None = None
    supported_model_types: Sequence[ModelType] = []


class DefaultModelEntity(BaseModel):
    """
    默认模型实体类
    """

    model: str
    model_type: ModelType
    provider: DefaultModelProviderEntity

    # pydantic 配置
    model_config = ConfigDict(protected_namespaces=())
