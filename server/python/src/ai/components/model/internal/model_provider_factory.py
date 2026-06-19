"""
模型提供者工厂类

迁移自 Alon: src/alon/components/model/internal/model_provider_factory.py

负责管理所有 AI 模型提供者的配置、验证、实例化等核心功能
"""

import os
from collections.abc import Sequence

from loguru import logger
from pydantic import BaseModel

from ai.components.model.errors import ProviderNotFoundError, UnsupportedProviderError
from ai.components.model.internal.entities.provider_entities import SimpleProviderConfig
from ai.components.model.internal.helper.position_helper import (
    get_provider_position_map,
    sort_to_dict_by_position_map,
)
from ai.components.plugin.client.plugin.entities.plugin import ModelProviderID
from ai_plugin.sdk.entities.model import AIModelEntity, ModelType
from ai_plugin.sdk.entities.model.provider import ProviderEntity, SimpleProviderEntity

# 延迟导入以避免循环依赖
# from ai.components.plugin.client.model_client import ModelClient

_logger = logger.bind(name=__name__)


class ModelProviderExtension(BaseModel):
    """
    模型提供者扩展类

    用于包装插件模型提供者实体，并添加位置信息，便于排序和管理
    """

    plugin_model_provider_entity: object  # PluginModelProviderEntity
    position: int | None = None  # 位置信息，用于排序


class ModelProviderFactory:
    """
    模型提供者工厂类

    负责管理所有 AI 模型提供者的配置、验证、实例化等核心功能。
    支持插件化的模型提供者管理，包括凭证验证、模型模式获取、模型实例创建等。
    """

    provider_position_map: dict[str, int]  # 提供者位置映射表

    def __init__(self, tenant_id: str) -> None:
        """
        初始化模型提供者工厂

        :param tenant_id: 租户 ID，用于多租户环境下的资源隔离
        """
        self.provider_position_map = {}
        self.tenant_id = tenant_id

        # 延迟导入以避免循环依赖
        from ai.components.plugin.client.model_client import ModelClient

        # 创建插件模型管理器客户端
        self.plugin_model_manager = ModelClient()

        if not self.provider_position_map:
            # 获取当前类文件的路径
            current_path = os.path.abspath(__file__)
            model_providers_path = os.path.dirname(current_path)

            # 获取 _position.yaml 文件中的提供者位置映射
            self.provider_position_map = get_provider_position_map(model_providers_path)

    async def get_providers(self) -> Sequence[ProviderEntity]:
        """
        获取所有模型提供者

        从插件系统中获取所有可用的模型提供者，并按配置的位置顺序排序

        :return: 模型提供者列表
        """
        # 获取插件模型提供者
        plugin_providers = await self.get_plugin_model_providers()

        # 将 PluginModelProviderEntity 转换为 ModelProviderExtension
        model_provider_extensions = []
        for provider in plugin_providers:
            model_provider_extensions.append(
                ModelProviderExtension(plugin_model_provider_entity=provider)
            )

        # 根据位置映射进行排序
        sorted_extensions = sort_to_dict_by_position_map(
            position_map=self.provider_position_map,
            data=model_provider_extensions,
            name_func=lambda x: x.plugin_model_provider_entity.declaration.provider,
        )

        return [
            extension.plugin_model_provider_entity.declaration
            for extension in sorted_extensions.values()
        ]

    async def get_plugin_model_providers(self) -> Sequence:
        """
        获取插件模型提供者列表

        :return: 插件模型提供者列表
        """

        plugin_model_providers = []

        # 从插件管理器获取模型提供者
        plugin_providers = await self.plugin_model_manager.fetch_model_providers(
            self.tenant_id
        )

        # 为每个提供者添加插件 ID 前缀，确保唯一性
        for provider in plugin_providers:
            provider.declaration.provider = (
                provider.plugin_id + "/" + provider.declaration.provider
            )
            plugin_model_providers.append(provider)

        return plugin_model_providers

    async def get_provider_schema(self, provider: str) -> ProviderEntity:
        """
        获取提供者模式配置

        :param provider: 提供者名称
        :return: 提供者实体配置
        """
        plugin_model_provider_entity = await self.get_plugin_model_provider(
            provider=provider
        )
        return plugin_model_provider_entity.declaration

    async def get_plugin_model_provider(self, provider: str):
        """
        获取插件模型提供者实体

        :param provider: 提供者名称
        :return: 插件模型提供者实体
        :raises ValueError: 当提供者不存在时抛出异常
        """

        # 如果提供者名称不包含插件 ID，自动添加默认格式
        if "/" not in provider:
            provider = str(ModelProviderID(provider))

        # 获取所有插件模型提供者
        plugin_model_provider_entities = await self.get_plugin_model_providers()

        # 查找指定的提供者
        plugin_model_provider_entity = next(
            (
                p
                for p in plugin_model_provider_entities
                if p.declaration.provider == provider
            ),
            None,
        )

        if not plugin_model_provider_entity:
            raise ProviderNotFoundError(provider)

        return plugin_model_provider_entity

    async def provider_credentials_validate(
        self, *, provider: str, credentials: dict
    ) -> dict:
        """
        验证模型提供者凭证

        :param provider: 提供者名称
        :param credentials: 提供者凭证信息
        :return: 验证通过的凭证信息
        :raises ValueError: 当提供者不存在凭证模式或验证失败时抛出异常
        """
        # 获取插件模型提供者
        plugin_model_provider_entity = await self.get_plugin_model_provider(
            provider=provider
        )

        # 获取提供者凭证模式并根据规则验证凭证
        provider_credential_schema = (
            plugin_model_provider_entity.declaration.provider_credential_schema
        )
        if not provider_credential_schema:
            raise UnsupportedProviderError(
                provider, f"提供者 {provider} 没有提供者凭证模式"
            )

        # TODO: 使用验证器验证提供者凭证模式
        # validator = ProviderCredentialSchemaValidator(provider_credential_schema)
        # filtered_credentials = validator.validate_and_filter(credentials)
        filtered_credentials = credentials

        # 通过插件管理器验证凭证的有效性
        result = await self.plugin_model_manager.validate_provider_credentials(
            tenant_id=self.tenant_id,
            user_id="unknown",
            plugin_id=plugin_model_provider_entity.plugin_id,
            provider=plugin_model_provider_entity.provider,
            credentials=filtered_credentials,
        )

        if not result:
            raise ValueError(f"提供者 {provider} 凭证验证失败")

        return filtered_credentials

    async def custom_model_credentials_validate(
        self,
        *,
        provider: str,
        model_type: ModelType,
        model: str,
        credentials: dict,
    ) -> dict:
        """
        验证自定义模型凭证

        :param provider: 提供者名称
        :param model_type: 模型类型
        :param model: 模型名称
        :param credentials: 提供者凭证信息
        :return: 验证通过的凭证信息
        :raises ValueError: 当提供者不存在凭证模式或验证失败时抛出异常
        """
        # 获取插件模型提供者
        plugin_model_provider_entity = await self.get_plugin_model_provider(
            provider=provider
        )

        # 获取模型凭证模式
        model_credential_schema = (
            plugin_model_provider_entity.declaration.model_credential_schema
        )
        if not model_credential_schema:
            raise UnsupportedProviderError(
                provider, f"提供者 {provider} 没有模型凭证模式"
            )

        # TODO: 使用验证器验证模型凭证模式
        # validator = ModelCredentialSchemaValidator(model_type, model_credential_schema)
        # filtered_credentials = validator.validate_and_filter(credentials)
        filtered_credentials = credentials

        # 通过插件管理器验证凭证的有效性
        result = await self.plugin_model_manager.validate_model_credentials(
            tenant_id=self.tenant_id,
            user_id="unknown",
            plugin_id=plugin_model_provider_entity.plugin_id,
            provider=plugin_model_provider_entity.provider,
            model_type=model_type,
            model=model,
            credentials=filtered_credentials,
        )

        if not result:
            raise ValueError(f"模型 {model} 凭证验证失败")

        return filtered_credentials

    async def get_model_schema(
        self,
        *,
        provider: str,
        model_type: ModelType,
        model: str,
        credentials: dict,
    ) -> AIModelEntity | None:
        """
        获取模型模式配置

        :param provider: 提供者名称
        :param model_type: 模型类型
        :param model: 模型名称
        :param credentials: 凭证信息
        :return: AI 模型实体配置，如果不存在返回 None
        """
        plugin_id, provider_name = self.get_plugin_id_and_provider_name_from_provider(
            provider
        )

        # 从插件管理器获取模型模式
        schema = await self.plugin_model_manager.get_model_schema(
            tenant_id=self.tenant_id,
            user_id="unknown",
            plugin_id=plugin_id,
            provider=provider_name,
            model_type=model_type,
            model=model,
            credentials=credentials or {},
        )

        return schema

    async def get_models(
        self,
        *,
        provider: str | None = None,
        model_type: ModelType | None = None,
        provider_configs: list[SimpleProviderConfig] | None = None,
    ) -> list[SimpleProviderEntity]:
        """
        获取指定类型的所有模型

        :param provider: 提供者名称（可选）
        :param model_type: 模型类型（可选）
        :param provider_configs: 提供者配置列表（可选）
        :return: 简化的提供者实体列表，包含模型信息
        """
        provider_configs = provider_configs or []

        # 扫描所有提供者
        plugin_model_provider_entities = await self.get_plugin_model_providers()

        # 将 provider_configs 转换为字典格式，便于查找
        provider_credentials_dict = {}
        for provider_config in provider_configs:
            provider_credentials_dict[provider_config.provider] = (
                provider_config.credentials
            )

        # 遍历所有模型提供者扩展
        providers = []
        for plugin_model_provider_entity in plugin_model_provider_entities:
            # 如果指定了提供者，进行过滤
            if (
                provider
                and plugin_model_provider_entity.declaration.provider != provider
            ):
                continue

            # 获取提供者模式
            provider_schema = plugin_model_provider_entity.declaration

            model_types = provider_schema.supported_model_types
            if model_type:
                # 检查提供者是否支持指定的模型类型
                if model_type not in model_types:
                    continue

                model_types = [model_type]

            # 收集指定类型的所有模型
            all_model_type_models = []
            for model_schema in provider_schema.models:
                if model_type and model_schema.model_type != model_type:
                    continue

                all_model_type_models.append(model_schema)

            # 创建简化的提供者模式并添加模型
            simple_provider_schema = provider_schema.to_simple_provider()
            simple_provider_schema.models.extend(all_model_type_models)

            providers.append(simple_provider_schema)

        return providers

    async def get_model_type_instance(self, provider: str, model_type: ModelType):
        """
        根据提供者名称和模型类型获取模型实例

        :param provider: 提供者名称
        :param model_type: 模型类型
        :return: 对应的模型实例
        :raises ValueError: 当模型类型不支持时抛出异常
        """
        from ai.components.model.model_providers.__base__.large_language_model import (
            LargeLanguageModelImpl,
        )

        plugin_id, provider_name = self.get_plugin_id_and_provider_name_from_provider(
            provider
        )

        # 获取插件模型提供者实体
        plugin_model_provider = await self.get_plugin_model_provider(provider)

        # 准备初始化参数
        init_params = {
            "tenant_id": self.tenant_id,
            "plugin_id": plugin_id,
            "provider_name": provider_name,
            "plugin_model_provider": plugin_model_provider,
        }

        # 根据模型类型创建对应的实例
        if model_type == ModelType.LLM:
            init_params["model_type"] = ModelType.LLM
            return LargeLanguageModelImpl(**init_params)
        else:
            raise UnsupportedProviderError(
                str(model_type), f"未支持的模型类型: {model_type}"
            )

    def get_plugin_id_and_provider_name_from_provider(
        self, provider: str
    ) -> tuple[str, str]:
        """
        从提供者名称中解析插件 ID 和提供者名称

        :param provider: 完整的提供者名称（格式：plugin_id/provider_name）
        :return: 插件 ID 和提供者名称的元组
        """
        provider_id = ModelProviderID(provider)
        return provider_id.plugin_id, provider_id.provider_name
