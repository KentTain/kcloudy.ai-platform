"""
供应商管理器类

迁移自 Alon: src/alon/components/model/internal/provider_manager.py

管理托管和自定义模型供应商，负责供应商配置的统一管理

使用 Redis 缓存来存储供应商配置，支持分布式环境下的缓存一致性
"""

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.components.model.errors import ProviderNotFoundError
from ai.components.model.internal.entities.provider_entities import (
    CustomConfiguration,
    CustomProviderConfiguration,
)
from ai.components.model.internal.model_provider_factory import ModelProviderFactory
from ai.models.plugin import PluginCredential
from ai.models.plugin_default_model import PluginDefaultModel
from ai.services.credential_service import credential_service
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
        self, tenant_id: str, use_cache: bool = True, db_session: AsyncSession | None = None
    ) -> ProviderConfigurations:
        """
        获取模型供应商配置集合

        :param tenant_id: 租户 ID
        :param use_cache: 是否使用缓存，默认 True
        :param db_session: 数据库会话（可选，用于凭证注入）
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
                            f"反序列化缓存数据失败 tenant_id={tenant_id}: {deserialize_error}, 将从插件加载"
                        )
                else:
                    _logger.debug(
                        f"Redis 缓存未命中 tenant_id={tenant_id}, 重新加载"
                    )
            except Exception as e:
                _logger.warning(
                    f"从 Redis 读取缓存失败 tenant_id={tenant_id}: {e}, 将从插件加载"
                )

        # 从插件 manifest 加载配置
        _logger.debug(f"从插件 manifest 加载配置 tenant_id={tenant_id}")

        model_provider_factory = ModelProviderFactory(tenant_id)
        provider_entities = await model_provider_factory.get_providers()

        provider_configurations = ProviderConfigurations(tenant_id=tenant_id)

        # 构造每个供应商的配置对象
        for provider_entity in provider_entities:
            # 创建空的自定义配置
            custom_configuration = CustomConfiguration(provider=None, models=[])

            # 构造供应商配置对象
            provider_configuration = ProviderConfiguration(
                provider=provider_entity,
                custom_configuration=custom_configuration,
                model_settings=[],
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

        # 注入插件凭证（如果提供了 session）
        await self._inject_plugin_credentials(
            session=db_session,
            provider_configurations=provider_configurations,
        )

        return provider_configurations

    async def _get_provider_model_bundle(
        self,
        tenant_id: str,
        provider: str,
        model_type: ModelType,
        db_session: AsyncSession | None = None,
    ) -> ProviderModelBundle:
        """
        获取供应商模型束

        :param tenant_id: 租户 ID
        :param provider: 供应商名称
        :param model_type: 模型类型
        :param db_session: 数据库会话（可选，用于凭证注入）
        :return: 供应商模型束
        """
        configurations = await self.get_configurations(tenant_id, db_session=db_session)
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

    async def get_default_provider_model_name(
        self,
        tenant_id: str,
        model_type: ModelType,
        db_session: AsyncSession | None = None,
    ) -> tuple[str | None, str | None]:
        """
        获取默认的供应商和模型名称

        :param tenant_id: 租户 ID
        :param model_type: 模型类型
        :param db_session: 数据库会话（可选，用于查询默认模型）
        :return: (供应商名称/plugin_id, 模型名称) 元组
        """
        # 从 plugin_default_models 表查询默认模型
        if db_session:
            default_model = await PluginDefaultModel.one_by_conditions(
                db_session,
                conditions=[
                    PluginDefaultModel.tenant_id == tenant_id,
                    PluginDefaultModel.model_type == model_type.value,
                    PluginDefaultModel.is_valid == True,
                ],
            )
            if default_model:
                # 优先返回 model_name，如果没有则返回 custom_model_name
                model_name = default_model.model_name or default_model.custom_model_name
                if model_name:
                    return default_model.plugin_id, model_name

        # 如果没有配置默认模型，则获取第一个可用的模型
        return await self._get_first_provider_first_model(tenant_id, model_type, db_session)

    async def _get_first_provider_first_model(
        self,
        tenant_id: str,
        model_type: ModelType,
        db_session: AsyncSession | None = None,
    ) -> tuple[str | None, str | None]:
        """
        获取第一个供应商的第一个模型

        :param tenant_id: 租户 ID
        :param model_type: 模型类型
        :param db_session: 数据库会话（可选，用于凭证注入）
        :return: (供应商名称, 模型名称) 元组
        """
        configurations = await self.get_configurations(tenant_id, db_session=db_session)
        models = await configurations.get_models(
            model_type=model_type, only_active=True
        )

        if not models:
            return None, None

        first_model = models[0]
        return first_model.provider.provider, first_model.model

    async def _inject_plugin_credentials(
        self,
        session: AsyncSession | None,
        provider_configurations: ProviderConfigurations,
    ) -> None:
        """
        从 PluginCredential 表注入凭证到 plugin provider

        :param session: 数据库会话
        :param provider_configurations: 供应商配置集合
        """
        if not session:
            return

        # 遍历所有 provider，找出 plugin 类型的 provider
        for provider_name, provider_config in provider_configurations.items():
            plugin_id = self._extract_plugin_id_from_provider(provider_name)
            if not plugin_id:
                continue

            # 从 PluginCredential 表查询默认凭证
            stmt = select(PluginCredential).where(
                PluginCredential.tenant_id == provider_configurations.tenant_id,
                PluginCredential.plugin_id == plugin_id,
                PluginCredential.is_default == True,
                PluginCredential.is_disabled == False,
            )
            result = await session.execute(stmt)
            credentials_list = result.scalars().all()

            if not credentials_list:
                continue

            # 获取默认凭证
            credential = credentials_list[0]

            # 获取凭证架构
            credentials_schema = self._extract_credentials_schema_from_provider(
                provider_config.provider
            )
            if not credentials_schema:
                continue

            # 解密凭证
            decrypted = credential_service.decrypt_credentials(
                credential.credentials or {},
                credentials_schema,
            )

            # 注入凭证到 custom_configuration.provider.credentials
            if provider_config.custom_configuration.provider is None:
                provider_config.custom_configuration.provider = CustomProviderConfiguration(
                    credentials=decrypted
                )
            else:
                provider_config.custom_configuration.provider.credentials = decrypted

            _logger.debug(
                f"已注入插件凭证 tenant_id={provider_configurations.tenant_id} "
                f"plugin_id={plugin_id} provider={provider_name}"
            )

    def _extract_plugin_id_from_provider(self, provider: str) -> str | None:
        """
        从 provider 名称中提取 plugin_id

        :param provider: provider 名称，例如 "alon/tongyi/openai"
        :return: plugin_id，例如 "alon/tongyi"，如果解析失败则返回 None
        """
        try:
            from ai.components.model.schema.provider_id import ModelProviderID

            provider_id = ModelProviderID(provider)
            return provider_id.plugin_id
        except Exception:
            return None

    def _extract_credentials_schema_from_provider(
        self, provider_entity: ProviderEntity
    ) -> list[dict] | None:
        """
        从 provider 实体中提取凭证架构

        将 CredentialFormSchema 转换为 CredentialService 需要的 dict 格式

        :param provider_entity: provider 实体
        :return: 凭证架构列表 [{"name": "api_key", "type": "secret-input", ...}, ...]
        """
        # 尝试从 provider_credential_schema 获取
        if provider_entity.provider_credential_schema:
            schemas = provider_entity.provider_credential_schema.credential_form_schemas
            if schemas:
                return self._convert_schemas_to_dict(schemas)

        # 尝试从 model_credential_schema 获取
        if provider_entity.model_credential_schema:
            schemas = provider_entity.model_credential_schema.credential_form_schemas
            if schemas:
                return self._convert_schemas_to_dict(schemas)

        return None

    def _convert_schemas_to_dict(
        self, schemas: list[CredentialFormSchema]
    ) -> list[dict]:
        """
        将 CredentialFormSchema 列表转换为 dict 列表

        Args:
            schemas: CredentialFormSchema 对象列表

        Returns:
            凭证架构字典列表
        """
        result = []
        for schema in schemas:
            item = {
                "name": schema.variable,
                "type": schema.type.value if hasattr(schema.type, "value") else str(schema.type),
                "required": schema.required,
            }
            if schema.options:
                item["options"] = [
                    {"value": opt.value, "label": opt.label}
                    for opt in schema.options
                ]
            result.append(item)

        return result

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
