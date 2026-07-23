"""模型配置服务"""

from __future__ import annotations

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.components.model.internal.model_provider_factory import ModelProviderFactory
from ai.models.plugin import PluginCredential
from ai.models.plugin import PluginConfig
from ai.models.plugin import PluginDefaultModel
from ai.models.plugin import PluginRuntimeState
from ai.schemas.model_config import (
    AvailableModelItemResponse,
    DefaultModelItemResponse,
    ModelConfigItemResponse,
    ModelConfigOverviewResponse,
    ModelSelectItemResponse,
    PluginAvailableModelsResponse,
    PluginWithModelsResponse,
)
from ai.services.plugin import plugin_default_model_service
from ai_plugin.sdk.entities.model import ModelType
from framework.common.ctx import get_tenant_id
from framework.tenant.plugin_protocols import get_plugin_installation_provider

_logger = logger.bind(name=__name__)


class ModelConfigService:
    """模型配置服务"""

    async def get_overview(self, session: AsyncSession, tenant_id: str) -> ModelConfigOverviewResponse:
        """获取模型配置页面聚合数据"""
        # 1. 从插件安装记录获取所有已安装插件
        provider = get_plugin_installation_provider()
        installations = await provider.get_tenant_installations(tenant_id)

        # 只取模型类型插件
        model_installations = [inst for inst in installations if inst.plugin_type == "model"]

        total_plugins = len(model_installations)

        # 2. 获取 AI 侧配置和运行时状态
        plugin_ids = [inst.plugin_id for inst in model_installations]
        if not plugin_ids:
            return ModelConfigOverviewResponse(
                total_plugins=0,
                configured_plugins=0,
                total_models=0,
            )

        # 获取运行时状态
        runtime_result = await session.execute(
            select(PluginRuntimeState).where(
                PluginRuntimeState.tenant_id == tenant_id,
                PluginRuntimeState.plugin_id.in_(plugin_ids),
            )
        )
        runtime_states = {st.plugin_id: st for st in runtime_result.scalars().all()}

        # 3. 从 ModelProviderFactory 获取模型列表
        model_provider_factory = ModelProviderFactory(tenant_id)
        try:
            provider_entities = await model_provider_factory.get_plugin_model_providers()
        except Exception as e:
            _logger.warning(f"获取模型提供者列表失败: {e}")
            provider_entities = []

        # 按 plugin_id 分组模型
        plugin_models_map: dict[str, list] = {}
        for provider_entity in provider_entities:
            pid = provider_entity.plugin_id
            if pid not in plugin_models_map:
                plugin_models_map[pid] = []
            plugin_models_map[pid].append(provider_entity)

        # 4. 获取所有默认模型
        default_models_result = await session.execute(
            select(PluginDefaultModel).where(
                PluginDefaultModel.tenant_id == tenant_id,
                PluginDefaultModel.is_valid == True,
            )
        )
        default_models_list = default_models_result.scalars().all()
        default_model_map: dict[str, PluginDefaultModel] = {
            dm.model_type: dm for dm in default_models_list
        }

        # 5. 组装插件和模型数据
        plugins_response: list[PluginWithModelsResponse] = []
        configured_plugins = 0
        total_models = 0

        for inst in model_installations:
            pid = inst.plugin_id
            plugin_providers = plugin_models_map.get(pid, [])

            if not plugin_providers:
                continue

            # 收集该插件下的所有模型
            models: list[ModelConfigItemResponse] = []
            for prov in plugin_providers:
                for model_schema in prov.declaration.models:
                    is_default = (
                        model_schema.model_type in default_model_map
                        and default_model_map[model_schema.model_type].model_name == model_schema.model
                        and default_model_map[model_schema.model_type].plugin_id == pid
                    )
                    models.append(
                        ModelConfigItemResponse(
                            model_name=model_schema.model,
                            model_label=model_schema.label.zh_Hans
                            if model_schema.label and model_schema.label.zh_Hans
                            else model_schema.model,
                            model_type=model_schema.model_type,
                            is_default=is_default,
                        )
                    )

            if not models:
                continue

            configured_plugins += 1
            total_models += len(models)

            # 获取状态
            runtime_state = runtime_states.get(pid)
            status = runtime_state.status if runtime_state else "inactive"

            # 插件名称
            plugin_name = pid.split("/")[-1] if "/" in pid else pid

            # 只返回已启动且已配置模型的插件
            if status != "active":
                continue

            plugins_response.append(
                PluginWithModelsResponse(
                    plugin_id=pid,
                    plugin_name=plugin_name,
                    status=status,
                    models=models,
                )
            )

        # 6. 组装默认模型展示
        default_models_response: list[DefaultModelItemResponse] = []
        for dm in default_models_list:
            default_models_response.append(
                DefaultModelItemResponse(
                    model_type=dm.model_type,
                    plugin_id=dm.plugin_id,
                    model_name=dm.model_name,
                    is_valid=dm.is_valid,
                )
            )

        return ModelConfigOverviewResponse(
            total_plugins=total_plugins,
            configured_plugins=configured_plugins,
            total_models=total_models,
            default_models=default_models_response,
            plugins=plugins_response,
        )

    async def get_available_models(
        self, session: AsyncSession, tenant_id: str, plugin_id: str
    ) -> PluginAvailableModelsResponse:
        """获取插件声明的所有模型（含启用状态）"""
        model_provider_factory = ModelProviderFactory(tenant_id)
        try:
            provider_entities = await model_provider_factory.get_plugin_model_providers()
        except Exception as e:
            _logger.warning(f"获取模型提供者列表失败: {e}")
            return PluginAvailableModelsResponse(models=[])

        # 获取已启用模型列表（从 provider configuration）
        enabled_model_names: set[str] = set()
        for prov in provider_entities:
            if prov.plugin_id == plugin_id:
                for model_schema in prov.declaration.models:
                    enabled_model_names.add(model_schema.model)

        models: list[AvailableModelItemResponse] = []
        for prov in provider_entities:
            if prov.plugin_id != plugin_id:
                continue
            for model_schema in prov.declaration.models:
                models.append(
                    AvailableModelItemResponse(
                        model_name=model_schema.model,
                        model_label=model_schema.label.zh_Hans
                        if model_schema.label and model_schema.label.zh_Hans
                        else model_schema.model,
                        model_type=model_schema.model_type,
                        is_enabled=model_schema.model in enabled_model_names,
                    )
                )

        return PluginAvailableModelsResponse(models=models)

    async def set_enabled_models(
        self, session: AsyncSession, tenant_id: str, plugin_id: str, model_names: list[str]
    ) -> None:
        """配置插件启用的模型"""
        # 当前实现中，模型启用状态由插件配置管理
        # 此方法为未来扩展预留，当前直接返回成功
        _logger.info(f"设置插件 {plugin_id} 的启用模型: {model_names}")

    async def get_models_by_type(
        self, session: AsyncSession, tenant_id: str, model_type: str
    ) -> list[ModelSelectItemResponse]:
        """按类型获取所有可选模型（含 plugin_id 和 provider 信息）"""
        model_provider_factory = ModelProviderFactory(tenant_id)
        try:
            provider_entities = await model_provider_factory.get_plugin_model_providers()
        except Exception as e:
            _logger.warning(f"获取模型提供者列表失败: {e}")
            return []

        models: list[ModelSelectItemResponse] = []
        for prov in provider_entities:
            plugin_id = prov.plugin_id
            provider_name = prov.declaration.provider
            plugin_name = plugin_id.split("/")[-1] if "/" in plugin_id else plugin_id

            for model_schema in prov.declaration.models:
                if model_schema.model_type != model_type:
                    continue
                models.append(
                    ModelSelectItemResponse(
                        plugin_id=plugin_id,
                        plugin_name=plugin_name,
                        provider=provider_name,
                        model_name=model_schema.model,
                        model_label=model_schema.label.zh_Hans
                        if model_schema.label and model_schema.label.zh_Hans
                        else model_schema.model,
                        model_type=model_schema.model_type,
                    )
                )

        return models

    async def batch_set_default_models(
        self, session: AsyncSession, tenant_id: str, items: list[dict]
    ) -> None:
        """批量设置默认模型，校验 embedding/rerank 同插件约束"""
        # 校验：如果同时设置 embedding 和 rerank，必须来自同一插件
        embedding_items = [i for i in items if i["model_type"] == ModelType.TEXT_EMBEDDING]
        rerank_items = [i for i in items if i["model_type"] == ModelType.RERANK]

        if embedding_items and rerank_items:
            embedding_plugin = embedding_items[0]["plugin_id"]
            rerank_plugin = rerank_items[0]["plugin_id"]
            if embedding_plugin != rerank_plugin:
                raise ValueError("embedding 和 rerank 默认模型必须来自同一插件")

        # 校验：embedding/rerank 已有默认模型时不可覆盖；其他类型允许覆盖
        immutable_types = {ModelType.TEXT_EMBEDDING, ModelType.RERANK}
        for item in items:
            if item["model_type"] in immutable_types:
                existing = await plugin_default_model_service.get_default_model(
                    session, tenant_id, item["model_type"]
                )
                if existing:
                    raise ValueError(
                        f"{item['model_type']} 类型默认模型设置后不可更改"
                    )

        # 逐一设置
        for item in items:
            await plugin_default_model_service.set_default_model(
                session=session,
                tenant_id=tenant_id,
                model_type=item["model_type"],
                plugin_id=item["plugin_id"],
                model_name=item.get("model_name"),
            )


model_config_service = ModelConfigService()
