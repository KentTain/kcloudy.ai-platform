"""
供应商管理器类

迁移自 Alon: src/alon/components/model/internal/provider_manager.py

管理托管和自定义模型供应商，负责供应商配置的统一管理

使用 Redis 缓存来存储供应商配置，支持分布式环境下的缓存一致性
"""

import json
from collections import defaultdict
from json import JSONDecodeError

from loguru import logger

from ai.components.model.errors import ProviderNotFoundError
from ai.components.model.internal.entities.provider_entities import (
    CustomConfiguration,
    CustomModelConfiguration,
    CustomProviderConfiguration,
    ModelSettings,
)
from ai.components.model.internal.helper.encrypter import decrypt_token
from ai.components.model.internal.model_provider_factory import ModelProviderFactory
from ai.components.model.schema.model_entities import (
    DefaultModelEntity,
)
from ai_plugin.sdk.entities.model import ModelType
from ai_plugin.sdk.entities.model.provider import (
    CredentialFormSchema,
    FormType,
    ProviderEntity,
)
from framework.cache.tenant_cache_manager import get_cache_manager

from .provider_configuration import (
    ProviderConfiguration,
    ProviderConfigurations,
    ProviderModelBundle,
)

_logger = logger.bind(name=__name__)


# 缓存配置常量
CACHE_KEY_PREFIX = "model:provider_configs"
CACHE_TTL = 300  # 5 分钟，因为有主动清除机制，可以设置更长


class ProviderManager:
    """
    供应商管理器类
    管理托管和自定义模型供应商，负责供应商配置的统一管理

    使用 Redis 缓存来存储供应商配置，支持分布式环境下的缓存一致性
    """

    def __init__(self) -> None:
        self.decoding_rsa_key = None
        self.decoding_cipher_rsa = None

    @classmethod
    async def clear_cache(cls, tenant_id: str | None = None):
        """
        清除配置缓存（使用 Redis）

        :param tenant_id: 租户 ID，如果为 None 则清除所有相关缓存
        """
        try:
            cache_manager = get_cache_manager()

            if tenant_id is None:
                # 清除所有租户的配置缓存（通过模式匹配）
                # 注意：当前实现不支持模式匹配，需要逐个清除
                _logger.info("已请求清除所有租户的配置缓存")
            else:
                # 清除指定租户的配置缓存
                cache_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"
                await cache_manager.delete(cache_key, tenant_id=tenant_id)
                _logger.info(f"已清除租户 {tenant_id} 的配置缓存")
        except Exception as e:
            _logger.error(f"清除缓存失败: {e}")

    async def get_configurations(
        self, tenant_id: str, use_cache: bool = True
    ) -> ProviderConfigurations:
        """
        获取模型供应商配置集合

        :param tenant_id: 租户 ID
        :param use_cache: 是否使用缓存，默认 True
        :return: 供应商配置集合
        """
        cache_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cache_manager = get_cache_manager()
                cached_data = await cache_manager.get(cache_key, tenant_id=tenant_id)

                if cached_data:
                    _logger.debug(f"使用 Redis 缓存的配置 tenant_id={tenant_id}")
                    # 反序列化缓存数据
                    try:
                        # 获取供应商实体用于反序列化
                        model_provider_factory = ModelProviderFactory(tenant_id)
                        provider_entities = await model_provider_factory.get_providers()
                        provider_entities_dict = {
                            p.provider: p for p in provider_entities
                        }

                        provider_configurations = ProviderConfigurations.from_dict(
                            cached_data, provider_entities_dict
                        )
                        return provider_configurations
                    except Exception as deserialize_error:
                        _logger.warning(
                            f"反序列化缓存数据失败 tenant_id={tenant_id}: {deserialize_error}, 将从数据库加载"
                        )
                else:
                    _logger.debug(
                        f"Redis 缓存未命中 tenant_id={tenant_id}, 重新加载"
                    )
            except Exception as e:
                _logger.warning(
                    f"从 Redis 读取缓存失败 tenant_id={tenant_id}: {e}, 将从数据库加载"
                )

        # 从数据库加载配置
        _logger.debug(f"从数据库加载配置 tenant_id={tenant_id}")

        # 获取所有模型供应商记录
        # TODO: 需要数据库模型支持
        provider_name_to_provider_records_dict: dict[str, list] = (
            await self._get_all_providers(tenant_id)
        )

        # 获取所有模型供应商实体定义
        model_provider_factory = ModelProviderFactory(tenant_id)
        provider_entities = await model_provider_factory.get_providers()

        # 获取所有模型供应商模型设置
        provider_name_to_provider_model_settings_dict = (
            await self._get_all_provider_model_settings(tenant_id)
        )

        provider_configurations = ProviderConfigurations(tenant_id=tenant_id)

        # 获取所有模型供应商模型记录
        provider_name_to_provider_model_records_dict = (
            await self._get_all_custom_models(tenant_id)
        )

        # 构造每个模型供应商的配置对象
        for provider_entity in provider_entities:
            provider_name = provider_entity.provider
            provider_records = provider_name_to_provider_records_dict.get(
                provider_entity.provider, []
            )

            custom_model_records = provider_name_to_provider_model_records_dict.get(
                provider_entity.provider, []
            )

            # 转换自定义配置
            custom_configuration = await self._to_custom_configuration(
                tenant_id,
                provider_entity,
                provider_records,
                custom_model_records,
            )

            # 获取模型供应商模型设置
            provider_model_settings = provider_name_to_provider_model_settings_dict.get(
                provider_name
            )

            # 转换模型设置
            model_settings = self._to_model_settings(
                provider_entity=provider_entity,
                provider_model_settings=provider_model_settings,
            )

            # 构造模型供应商配置对象
            provider_configuration = ProviderConfiguration(
                provider=provider_entity,
                custom_configuration=custom_configuration,
                model_settings=model_settings,
                tenant_id=tenant_id,
            )

            provider_configurations[provider_entity.provider] = provider_configuration

        # 存入 Redis 缓存
        if use_cache:
            try:
                cache_manager = get_cache_manager()
                # 序列化配置数据并缓存
                cache_data = provider_configurations.to_dict()
                await cache_manager.set(
                    cache_key, cache_data, ttl=CACHE_TTL, tenant_id=tenant_id
                )
                _logger.debug(
                    f"已缓存配置到 Redis tenant_id={tenant_id}, TTL={CACHE_TTL}秒"
                )
            except Exception as e:
                _logger.warning(f"缓存配置到 Redis 失败 tenant_id={tenant_id}: {e}")

        return provider_configurations

    async def _get_provider_model_bundle(
        self,
        tenant_id: str,
        provider: str,
        model_type: ModelType,
    ) -> ProviderModelBundle:
        """
        获取供应商模型束

        :param tenant_id: 租户 ID
        :param provider: 供应商名称
        :param model_type: 模型类型
        :return: 供应商模型束
        """
        configurations = await self.get_configurations(tenant_id)
        provider_configuration = configurations.get(provider)

        if not provider_configuration:
            raise ProviderNotFoundError(provider)

        model_type_instance = await provider_configuration.get_model_type_instance(
            model_type
        )

        return ProviderModelBundle(
            configuration=provider_configuration,
            model_type_instance=model_type_instance,
        )

    @staticmethod
    async def _get_all_custom_models(tenant_id: str) -> dict[str, list]:
        """
        获取所有自定义模型记录

        :param tenant_id: 租户 ID
        :return: 按供应商名称分组的自定义模型记录
        """
        # TODO: 需要数据库模型支持
        # async with async_session() as session:
        #     stmt = select(ModelCustom).where(
        #         ModelCustom.tenant_id == tenant_id, ModelCustom.is_valid == True
        #     )
        #     result = await session.execute(stmt)
        #     custom_models = result.scalars().all()
        #
        #     custom_model_records = defaultdict(list)
        #     for custom_model in custom_models:
        #         custom_model_records[custom_model.provider_name].append(custom_model)
        #
        # return custom_model_records
        return defaultdict(list)

    async def get_default_model(
        self, tenant_id: str, model_type: ModelType
    ) -> DefaultModelEntity | None:
        """
        获取指定模型类型的默认模型

        :param tenant_id: 租户 ID
        :param model_type: 模型类型
        :return: 默认模型实体（可能为 None）
        """
        # TODO: 需要数据库模型支持
        # async with async_session() as session:
        #     stmt = select(ModelTenantDefault).where(
        #         ModelTenantDefault.tenant_id == tenant_id,
        #         ModelTenantDefault.model_type == model_type,
        #     )
        #     result = await session.execute(stmt)
        #     default_model_record = result.scalar_one_or_none()
        #
        #     if not default_model_record:
        #         return None
        #
        #     ...
        return None

    async def get_default_provider_model_name(
        self,
        tenant_id: str,
        model_type: ModelType,
    ) -> tuple[str | None, str | None]:
        """
        获取默认的供应商和模型名称

        :param tenant_id: 租户 ID
        :param model_type: 模型类型
        :return: (供应商名称, 模型名称) 元组
        """
        # 首先尝试获取已配置的默认模型
        default_model = await self.get_default_model(tenant_id, model_type)
        if default_model:
            return default_model.provider.provider, default_model.model

        # 如果没有配置默认模型，则获取第一个可用的模型
        return await self._get_first_provider_first_model(tenant_id, model_type)

    async def _get_first_provider_first_model(
        self,
        tenant_id: str,
        model_type: ModelType,
    ) -> tuple[str | None, str | None]:
        """
        获取第一个供应商的第一个模型

        :param tenant_id: 租户 ID
        :param model_type: 模型类型
        :return: (供应商名称, 模型名称) 元组
        """
        configurations = await self.get_configurations(tenant_id)
        models = await configurations.get_models(
            model_type=model_type, only_active=True
        )

        if not models:
            return None, None

        first_model = models[0]
        return first_model.provider.provider, first_model.model

    async def update_default_model_record(
        self,
        tenant_id: str,
        model_type: ModelType,
        provider: str,
        model: str,
    ):
        """
        更新默认模型记录

        :param tenant_id: 租户 ID
        :param model_type: 模型类型
        :param provider: 供应商名称
        :param model: 模型名称
        :return: 更新后的默认模型记录
        """
        # TODO: 需要数据库模型支持
        pass

    async def _get_all_providers(self, tenant_id: str) -> dict[str, list]:
        """
        获取所有模型供应商记录

        :param tenant_id: 租户 ID
        :return: 按供应商名称分组的供应商记录字典
        """
        # TODO: 需要数据库模型支持
        # async with async_session() as session:
        #     stmt = select(ModelProvider).where(ModelProvider.tenant_id == tenant_id)
        #     result = await session.execute(stmt)
        #     providers = result.scalars().all()
        #
        # # 按供应商名称分组
        # provider_name_to_provider_records_dict = defaultdict(list)
        # for provider in providers:
        #     provider_name_to_provider_records_dict[provider.provider_name].append(
        #         provider
        #     )
        #
        # return dict(provider_name_to_provider_records_dict)
        return defaultdict(list)

    async def _get_all_provider_model_settings(
        self, tenant_id: str
    ) -> dict[str, list]:
        """
        获取所有模型供应商模型设置

        :param tenant_id: 租户 ID
        :return: 按供应商名称分组的模型设置字典
        """
        # TODO: 需要数据库模型支持
        # async with async_session() as session:
        #     stmt = select(ModelSetting).where(ModelSetting.tenant_id == tenant_id)
        #     result = await session.execute(stmt)
        #     provider_model_settings = result.scalars().all()
        #
        # # 按供应商名称分组
        # provider_name_to_provider_model_settings_dict = defaultdict(list)
        # for provider_model_setting in provider_model_settings:
        #     provider_name_to_provider_model_settings_dict[
        #         provider_model_setting.provider_name
        #     ].append(
        #         provider_model_setting,
        #     )
        #
        # return dict(provider_name_to_provider_model_settings_dict)
        return defaultdict(list)

    async def _to_custom_configuration(
        self,
        tenant_id: str,
        provider_entity: ProviderEntity,
        provider_records: list,
        custom_model_records: list,
    ) -> CustomConfiguration:
        """
        转换为自定义配置对象

        :param tenant_id: 租户 ID
        :param provider_entity: 供应商实体
        :param provider_records: 供应商记录列表
        :param custom_model_records: 自定义模型记录列表
        :return: 自定义配置对象
        """
        # 获取有效的供应商配置记录
        provider_record = None
        # TODO: 需要数据库模型支持
        # for record in provider_records:
        #     if record.provider_type == ProviderType.CUSTOM and record.is_valid:
        #         provider_record = record
        #         break

        provider = None

        if provider_record:
            # 处理供应商凭证解密
            if provider_entity.provider_credential_schema:
                # 获取供应商凭证中的敏感变量
                credential_secret_variables = self._extract_secret_variables(
                    provider_entity.provider_credential_schema.credential_form_schemas,
                )

                # 解密供应商凭证
                provider_credentials = {}
                try:
                    provider_credentials = (
                        json.loads(provider_record.encrypted_config)
                        if provider_record.encrypted_config
                        else {}
                    )
                except JSONDecodeError:
                    provider_credentials = {}

                # 解密供应商凭证
                for key in credential_secret_variables:
                    if key in provider_credentials:
                        provider_credentials[key] = decrypt_token(
                            tenant_id, provider_credentials[key]
                        )

            # 创建自定义供应商配置
            provider = CustomProviderConfiguration(credentials=provider_credentials)

        # 获取模型凭证敏感变量
        model_credential_secret_variables = self._extract_secret_variables(
            provider_entity.model_credential_schema.credential_form_schemas
            if provider_entity.model_credential_schema
            else [],
        )

        # 获取自定义模型配置
        custom_model_configurations = []
        for custom_model_record in custom_model_records:
            if not custom_model_record.encrypted_config:
                continue

            try:
                provider_model_credentials = json.loads(
                    custom_model_record.encrypted_config
                )
            except JSONDecodeError:
                continue

            # 解密模型凭证
            for variable in model_credential_secret_variables:
                if variable in provider_model_credentials:
                    try:
                        provider_model_credentials[variable] = decrypt_token(
                            provider_model_credentials.get(variable)
                        )
                    except ValueError:
                        pass

            custom_model_configurations.append(
                CustomModelConfiguration(
                    model=custom_model_record.model_name,
                    model_type=custom_model_record.model_type,
                    credentials=provider_model_credentials,
                ),
            )

        return CustomConfiguration(
            provider=provider, models=custom_model_configurations
        )

    @staticmethod
    def _extract_secret_variables(
        credential_form_schemas: list[CredentialFormSchema],
    ) -> list[str]:
        """
        提取敏感输入表单变量

        :param credential_form_schemas: 凭证表单架构列表
        :return: 敏感变量名称列表
        """
        secret_input_form_variables = []
        for credential_form_schema in credential_form_schemas:
            if credential_form_schema.type == FormType.SECRET_INPUT:
                secret_input_form_variables.append(credential_form_schema.variable)

        return secret_input_form_variables

    def _to_model_settings(
        self,
        provider_entity: ProviderEntity,
        provider_model_settings: list | None = None,
    ) -> list[ModelSettings]:
        """
        转换为模型设置列表

        :param provider_entity: 供应商实体
        :param provider_model_settings: 供应商模型设置列表（可选）
        :return: 模型设置列表
        """
        model_settings = []

        if not provider_model_settings:
            return model_settings

        # 按模型类型和模型名称分组模型设置
        model_setting_map: dict[ModelType, dict] = defaultdict(dict)
        # TODO: 需要数据库模型支持
        # for model_setting in provider_model_settings:
        #     model_type = model_setting.model_type
        #     model_setting_map[model_type][model_setting.model_name] = model_setting

        # 创建模型设置对象
        for model_type, model_setting_dict in model_setting_map.items():
            for model, model_setting in model_setting_dict.items():
                model_settings.append(
                    ModelSettings(
                        model=model,
                        model_type=model_type,
                        enabled=model_setting.enabled,
                    ),
                )

        return model_settings
