"""插件配置提供者实现

PluginConfigProvider 协议在 AI 模块的具体实现。
Tenant 模块通过此实现配置插件凭证，不直接访问 AI Schema。
"""
from loguru import logger

from ai.services.plugin import plugin_config_service
from framework.database.dependencies import get_task_session
from framework.tenant.plugin_protocols import PluginConfigDTO, PluginConfigProvider

_logger = logger.bind(name=__name__)


class PluginConfigProviderImpl(PluginConfigProvider):
    """插件配置提供者实现

    本地部署时直接访问数据库，委托给 plugin_config_service。
    每个方法使用独立的 Session 管理事务。
    """

    async def configure_plugin(
        self,
        tenant_id: str,
        plugin_id: str,
        plugin_config: dict | None,
        runtime_config: dict | None,
    ) -> PluginConfigDTO:
        """配置插件凭证"""
        async with get_task_session() as session:
            response = await plugin_config_service.config_plugin(
                session=session,
                tenant_id=tenant_id,
                plugin_id=plugin_id,
                plugin_config=plugin_config,
                runtime_config=runtime_config,
            )
            _logger.info(f"插件凭证已配置: {plugin_id}")
            return PluginConfigDTO(
                plugin_id=response.plugin_id,
                plugin_config=plugin_config,
                runtime_config=runtime_config,
            )


# 单例实例
plugin_config_provider_impl = PluginConfigProviderImpl()
