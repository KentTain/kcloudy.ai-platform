"""
模型供应商配置类

迁移自 Alon: src/alon/components/model/internal/provider_configuration.py

管理单个供应商的配置信息，包括凭证和模型设置
"""

import datetime
from collections import defaultdict
from collections.abc import Iterator, Sequence
from json import JSONDecodeError
import json

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from ai.components.model.constants import HIDDEN_VALUE
from ai.components.model.internal.entities.provider_entities import (
    CustomConfiguration,
    ModelSettings,
)
from ai.components.model.internal.helper.encrypter import (
    decrypt_token,
    encrypt_token,
    obfuscated_token,
)
from ai.components.model.internal.model_provider_factory import ModelProviderFactory
from ai.components.model.schema.model_entities import (
    ModelStatus,
    ModelWithProviderEntity,
    SimpleModelProviderEntity,
)
from ai.components.plugin.client.plugin.entities.plugin import ModelProviderID
from ai_plugin.sdk.entities.model import AIModelEntity, FetchFrom, ModelType
from ai_plugin.sdk.entities.model.provider import (
    CredentialFormSchema,
    FormType,
    ProviderEntity,
)

_logger = logger.bind(name=__name__)


# 缓存原始供应商配置方法
original_provider_configurate_methods: dict[str, list] = {}


class ProviderConfiguration(BaseModel):
    """
    模型供应商配置类
    管理单个供应商的配置信息，包括凭证和模型设置
    """

    tenant_id: str  # 租户ID
    provider: ProviderEntity  # 供应商实体信息
    custom_configuration: CustomConfiguration  # 自定义配置
    model_settings: list[ModelSettings]  # 模型设置列表

    # pydantic配置
    model_config = ConfigDict(protected_namespaces=())

    def __init__(self, **data):
        super().__init__(**data)

        # 缓存原始供应商配置方法
        if self.provider.provider not in original_provider_configurate_methods:
            original_provider_configurate_methods[self.provider.provider] = []
            for configurate_method in self.provider.configurate_methods:
                original_provider_configurate_methods[self.provider.provider].append(
                    configurate_method
                )

    def get_current_credentials(self, model_type: ModelType, model: str) -> dict | None:
        """
        获取当前有效凭证

        :param model_type: 模型类型
        :param model: 模型名称
        :return: 凭证字典（可能为None）
        """
        # 检查模型是否被管理员禁用
        if self.model_settings:
            for model_setting in self.model_settings:
                if (
                    model_setting.model_type == model_type
                    and model_setting.model == model
                ):
                    if not model_setting.enabled:
                        raise ValueError(f"模型 {model} 已被禁用")

        credentials = None

        if self.custom_configuration.models:
            for custom_model in self.custom_configuration.models:
                if (
                    custom_model.model == model
                    and custom_model.model_type == model_type
                ):
                    credentials = custom_model.credentials
                    break

        # 获取自定义配置凭证
        if not credentials and self.custom_configuration.provider:
            credentials = self.custom_configuration.provider.credentials

        return credentials

    def is_custom_configuration_available(self) -> bool:
        """
        检查自定义模型供应商凭证是否可用

        :return: 是否可用
        """
        return (
            self.custom_configuration.provider is not None
            or len(self.custom_configuration.models) > 0
        )

    async def get_custom_credentials(self, obfuscated: bool = False) -> dict | None:
        """
        获取自定义模型供应商凭证

        :param obfuscated: 是否混淆敏感凭证
        :return: 凭证字典（可能为None）
        """
        if self.custom_configuration.provider is None:
            return None

        credentials = self.custom_configuration.provider.credentials
        if not obfuscated:
            return credentials

        # 混淆敏感凭证信息
        return self.__obfuscated_credentials(
            credentials=credentials,
            credential_form_schemas=self.provider.provider_credential_schema.credential_form_schemas
            if self.provider.provider_credential_schema
            else [],
        )

    async def custom_credentials_validate(
        self, credentials: dict
    ) -> tuple[dict | None, dict]:
        """
        验证自定义模型供应商凭证

        :param credentials: 供应商凭证
        :return: 数据库记录和验证后的凭证
        """
        # TODO: 需要数据库模型支持
        # provider_record = await self._get_custom_provider_credentials()

        # 获取凭证表单中的敏感变量
        provider_credential_secret_variables = self.__extract_secret_variables(
            self.provider.provider_credential_schema.credential_form_schemas
            if self.provider.provider_credential_schema
            else [],
        )

        # 处理已有凭证记录的情况
        provider_record = None
        original_credentials = {}

        # 处理隐藏值：如果新凭证中有[__HIDDEN__]标记，使用原始值
        for key, value in credentials.items():
            if key in provider_credential_secret_variables:
                if value == HIDDEN_VALUE and key in original_credentials:
                    credentials[key] = decrypt_token(
                        self.tenant_id, original_credentials[key]
                    )

        # 通过供应商工厂验证凭证
        model_provider_factory = ModelProviderFactory(self.tenant_id)
        credentials = await model_provider_factory.provider_credentials_validate(
            provider=self.provider.provider,
            credentials=credentials,
        )

        # 加密敏感凭证
        for key, value in credentials.items():
            if key in provider_credential_secret_variables:
                credentials[key] = encrypt_token(self.tenant_id, value)

        return provider_record, credentials

    async def custom_model_credentials_validate(
        self, model_type: ModelType, model: str, credentials: dict
    ) -> dict:
        """
        验证自定义模型供应商凭证

        :param credentials: 供应商凭证
        :return: 验证后的凭证
        """
        # TODO: 需要数据库模型支持
        custom_model_record = None

        # 获取凭证表单中的敏感变量
        model_credential_secret_variables = self.__extract_secret_variables(
            self.provider.model_credential_schema.credential_form_schemas
            if self.provider.model_credential_schema
            else [],
        )

        # 处理已有凭证记录的情况
        original_credentials = {}

        # 处理隐藏值：如果新凭证中有[__HIDDEN__]标记，使用原始值
        for key, value in credentials.items():
            if key in model_credential_secret_variables:
                if value == HIDDEN_VALUE and key in original_credentials:
                    credentials[key] = decrypt_token(
                        self.tenant_id, original_credentials[key]
                    )

        # 通过供应商工厂验证凭证
        model_provider_factory = ModelProviderFactory(self.tenant_id)
        credentials = await model_provider_factory.custom_model_credentials_validate(
            provider=self.provider.provider,
            model_type=model_type,
            model=model,
            credentials=credentials,
        )

        # 加密敏感凭证
        for key, value in credentials.items():
            if key in model_credential_secret_variables:
                credentials[key] = encrypt_token(self.tenant_id, value)

        return credentials

    async def add_or_update_custom_credentials(self, credentials: dict) -> None:
        """
        新增或更新自定义供应商凭证

        TODO: 需要数据库模型支持
        """
        # provider_record, credentials = await self.custom_credentials_validate(credentials)

        # 保存供应商凭证到数据库
        # ...

        # 清除缓存
        from ai.components.model.internal.provider_manager import ProviderManager

        await ProviderManager.clear_cache(self.tenant_id)

    async def delete_custom_credentials(self) -> None:
        """
        删除自定义供应商凭证

        TODO: 需要数据库模型支持
        """
        # 清除缓存
        from ai.components.model.internal.provider_manager import ProviderManager

        await ProviderManager.clear_cache(self.tenant_id)

    async def get_model_type_instance(self, model_type: ModelType):
        """
        获取当前模型类型实例

        :param model_type: 模型类型
        :return: AI模型实例
        """
        model_provider_factory = ModelProviderFactory(self.tenant_id)

        # 获取指定类型的模型实例
        return await model_provider_factory.get_model_type_instance(
            provider=self.provider.provider,
            model_type=model_type,
        )

    async def get_model_schema(
        self, model_type: ModelType, model: str, credentials: dict
    ) -> AIModelEntity | None:
        """
        获取模型架构信息
        """
        model_provider_factory = ModelProviderFactory(self.tenant_id)
        return await model_provider_factory.get_model_schema(
            provider=self.provider.provider,
            model_type=model_type,
            model=model,
            credentials=credentials,
        )

    def __extract_secret_variables(
        self, credential_form_schemas: list[CredentialFormSchema]
    ) -> list[str]:
        """
        提取凭证表单中的敏感变量

        :param credential_form_schemas: 凭证表单架构列表
        :return: 敏感变量名称列表
        """
        secret_input_form_variables = []
        for credential_form_schema in credential_form_schemas:
            if credential_form_schema.type == FormType.SECRET_INPUT:
                secret_input_form_variables.append(credential_form_schema.variable)

        return secret_input_form_variables

    def __obfuscated_credentials(
        self, credentials: dict, credential_form_schemas: list[CredentialFormSchema]
    ) -> dict:
        """
        混淆敏感凭证信息

        :param credentials: 原始凭证
        :param credential_form_schemas: 凭证表单架构列表
        :return: 混淆后的凭证
        """
        # 获取凭证表单中的敏感变量
        credential_secret_variables = self.__extract_secret_variables(
            credential_form_schemas
        )

        # 混淆敏感凭证
        copy_credentials = credentials.copy()
        for key, value in copy_credentials.items():
            if key in credential_secret_variables:
                copy_credentials[key] = obfuscated_token(value)

        return copy_credentials

    async def get_provider_model(
        self,
        model_type: ModelType,
        model: str,
        only_active: bool = False,
    ) -> ModelWithProviderEntity | None:
        """
        获取指定的供应商模型

        :param model_type: 模型类型
        :param model: 模型名称
        :param only_active: 是否只返回活动模型
        :return: 供应商模型实体（可能为None）
        """
        provider_models = await self.get_provider_models(model_type, only_active, model)

        for provider_model in provider_models:
            if provider_model.model == model:
                return provider_model

        return None

    async def get_provider_models(
        self,
        model_type: ModelType | None = None,
        only_active: bool = False,
        model: str | None = None,
    ) -> list[ModelWithProviderEntity]:
        """
        获取供应商支持的模型列表

        :param model_type: 模型类型（可选）
        :param only_active: 是否只返回活动模型
        :param model: 模型名称（可选）
        :return: 供应商模型列表
        """
        model_provider_factory = ModelProviderFactory(self.tenant_id)
        provider_schema = await model_provider_factory.get_provider_schema(
            self.provider.provider
        )

        # 确定要查询的模型类型
        model_types: list[ModelType] = []
        if model_type:
            model_types.append(model_type)
        else:
            model_types = list(provider_schema.supported_model_types)

        # 按模型类型和模型名称分组模型设置
        model_setting_map: defaultdict[ModelType, dict[str, ModelSettings]] = (
            defaultdict(dict)
        )
        for model_setting in self.model_settings:
            model_setting_map[model_setting.model_type][model_setting.model] = (
                model_setting
            )

        # 获取自定义供应商模型列表
        provider_models = await self._get_custom_provider_models(
            model_types=model_types,
            provider_schema=provider_schema,
            model_setting_map=model_setting_map,
            model=model,
        )

        # 过滤只返回活动模型
        if only_active:
            provider_models = [
                m for m in provider_models if m.status == ModelStatus.ACTIVE
            ]

        return provider_models

    async def _get_custom_provider_models(
        self,
        model_types: Sequence[ModelType],
        provider_schema: ProviderEntity,
        model_setting_map: dict[ModelType, dict[str, ModelSettings]],
        model: str | None = None,
    ) -> list[ModelWithProviderEntity]:
        """
        获取自定义供应商模型列表

        :param model_types: 模型类型列表
        :param provider_schema: 供应商架构
        :param model_setting_map: 模型设置映射
        :return: 供应商模型列表
        """
        from ai_plugin.sdk.entities.model.provider import ModelPosition

        provider_models = []

        # 获取当前凭证信息
        credentials = None
        if self.custom_configuration.provider:
            credentials = self.custom_configuration.provider.credentials

        # 遍历模型类型构建模型列表
        for model_type in model_types:
            if model_type not in self.provider.supported_model_types:
                continue

            for m in provider_schema.models:
                if m.model_type != model_type:
                    continue

                # 确定模型状态：有凭证则为活动状态，否则为未配置状态
                status = ModelStatus.ACTIVE if credentials else ModelStatus.NO_CONFIGURE

                # 检查模型设置中的启用状态
                if (
                    m.model_type in model_setting_map
                    and m.model in model_setting_map[m.model_type]
                ):
                    model_setting = model_setting_map[m.model_type][m.model]
                    if model_setting.enabled is False:
                        status = ModelStatus.DISABLED

                # 构建供应商模型实体
                provider_models.append(
                    ModelWithProviderEntity(
                        model=m.model,
                        label=m.label,
                        model_type=m.model_type,
                        features=m.features,
                        fetch_from=m.fetch_from,
                        model_properties=m.model_properties,
                        deprecated=m.deprecated,
                        provider=SimpleModelProviderEntity(self.provider),
                        status=status,
                    ),
                )

            # 自定义模型
            for model_configuration in self.custom_configuration.models:
                if model_configuration.model_type not in model_types:
                    continue
                if model and model != model_configuration.model:
                    continue

                if model_configuration.model_type != model_type:
                    continue
                try:
                    custom_model_schema = await self.get_model_schema(
                        model_type=model_configuration.model_type,
                        model=model_configuration.model,
                        credentials=model_configuration.credentials,
                    )
                except Exception as ex:
                    _logger.warning(f"获取自定义模型架构失败, {ex}")
                    continue

                if not custom_model_schema:
                    continue

                status = ModelStatus.ACTIVE
                if (
                    custom_model_schema.model_type in model_setting_map
                    and custom_model_schema.model
                    in model_setting_map[custom_model_schema.model_type]
                ):
                    model_setting = model_setting_map[custom_model_schema.model_type][
                        custom_model_schema.model
                    ]
                    if model_setting.enabled is False:
                        status = ModelStatus.DISABLED

                provider_models.append(
                    ModelWithProviderEntity(
                        model=custom_model_schema.model,
                        label=custom_model_schema.label,
                        model_type=custom_model_schema.model_type,
                        features=custom_model_schema.features,
                        fetch_from=FetchFrom.CUSTOMIZABLE_MODEL,
                        model_properties=custom_model_schema.model_properties,
                        deprecated=custom_model_schema.deprecated,
                        provider=SimpleModelProviderEntity(self.provider),
                        status=status,
                    ),
                )

        return provider_models


class ProviderConfigurations(BaseModel):
    """
    模型供应商配置集合类
    管理多个供应商的配置信息
    """

    tenant_id: str  # 租户ID
    configurations: dict[str, ProviderConfiguration] = Field(
        default_factory=dict
    )  # 供应商配置字典

    def __init__(self, tenant_id: str):
        super().__init__(tenant_id=tenant_id)

    async def get_models(
        self,
        provider: str | None = None,
        model_type: ModelType | None = None,
        only_active: bool = False,
    ) -> list[ModelWithProviderEntity]:
        """
        获取可用模型列表

        :param provider: 供应商名称
        :param model_type: 模型类型
        :param only_active: 是否只返回活动模型
        :return: 模型列表
        """
        all_models = []
        for provider_configuration in self.values():
            # 根据供应商名称过滤
            if provider and provider_configuration.provider.provider != provider:
                continue

            models = await provider_configuration.get_provider_models(
                model_type, only_active
            )
            all_models.extend(models)

        return all_models

    def to_list(self) -> list[ProviderConfiguration]:
        """
        转换为供应商配置列表

        :return: 供应商配置列表
        """
        return list(self.values())

    def __getitem__(self, key):
        if "/" not in key:
            key = str(ModelProviderID(key))

        return self.configurations[key]

    def __setitem__(self, key, value):
        self.configurations[key] = value

    def __iter__(self):
        return iter(self.configurations)

    def values(self) -> Iterator[ProviderConfiguration]:
        return iter(self.configurations.values())

    def get(self, key, default=None) -> ProviderConfiguration | None:
        if "/" not in key:
            key = str(ModelProviderID(key))

        return self.configurations.get(key, default)


class ProviderModelBundle(BaseModel):
    """
    供应商模型束
    包含供应商配置和模型类型实例
    """

    configuration: ProviderConfiguration  # 供应商配置
    model_type_instance: object  # 模型类型实例 (AIModelImpl)

    # pydantic配置
    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())
