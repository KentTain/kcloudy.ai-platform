from abc import ABC, abstractmethod

from ai_plugin.sdk.entities.model import AIModelEntity, ModelType
from ai_plugin.sdk.entities.model.provider import ProviderEntity
from ai_plugin.sdk.interfaces.model.ai_model import AIModel


class ModelProvider(ABC):
    """模型提供者基类"""

    provider_schema: ProviderEntity
    model_instance_map: dict[ModelType, AIModel]

    def __init__(
        self,
        provider_schemas: ProviderEntity,
        model_instance_map: dict[ModelType, AIModel],
    ):
        """
        初始化模型提供者

        :param provider_schemas: 提供者架构
        :param model_instance_map: 模型实例映射表
        """
        self.provider_schema = provider_schemas
        self.model_instance_map = model_instance_map

    @abstractmethod
    def validate_provider_credentials(self, credentials: dict) -> None:
        """
        验证提供者凭证
        您可以选择任何模型类型的validate_credentials方法或自己实现验证方法，
        例如：获取模型列表API

        如果验证失败，抛出异常

        :param credentials: 提供者凭证，凭证格式在`provider_credential_schema`中定义
        """
        raise NotImplementedError

    def get_provider_schema(self) -> ProviderEntity:
        """
        获取提供者架构

        :return: 提供者架构
        """
        return self.provider_schema

    def models(self, model_type: ModelType) -> list[AIModelEntity]:
        """
        获取指定模型类型的所有模型

        :param model_type: 在`ModelType`中定义的模型类型
        :return: 模型列表
        """
        provider_schema = self.get_provider_schema()
        if model_type not in provider_schema.supported_model_types:
            return []

        # 获取模型类型的模型实例
        model_instance = self.get_model_instance(model_type)

        # 获取预定义模型 (predefined_models)
        models = model_instance.predefined_models()

        # 返回模型列表
        return models

    def get_model_instance(self, model_type: ModelType) -> AIModel:
        """
        获取模型实例

        :param model_type: 在`ModelType`中定义的模型类型
        :return: 模型实例
        """
        if model_type in self.model_instance_map:
            return self.model_instance_map[model_type]

        raise ValueError(f"Model instance not found for model type: {model_type}")
