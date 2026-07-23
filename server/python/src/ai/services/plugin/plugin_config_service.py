"""插件配置服务

提供插件配置、测试连接、启动、停止等业务逻辑。

职责分离说明：
- tenant 模块负责"有什么"（插件定义、安装记录）
- ai 模块负责"怎么用"（配置、启动、停止）
"""

from datetime import datetime
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.plugin import PluginConfig
from ai.schemas.plugin_config import (
    PluginConfigResponse,
    PluginStartResponse,
    PluginStopResponse,
    PluginTestResponse,
)
from ai.services.plugin import plugin_management_service
from framework.common.ctx import get_tenant_id

_logger = logger.bind(name=__name__)


class PluginConfigService:
    """插件配置服务"""

    async def config_plugin(
        self,
        session: AsyncSession,
        tenant_id: str,
        plugin_id: str,
        plugin_config: dict | None,
        runtime_config: dict | None,
    ) -> PluginConfigResponse:
        """
        配置插件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID
            plugin_config: 插件配置（如 API Key、Endpoint 等）
            runtime_config: 运行时配置（如超时时间、重试次数等）

        Returns:
            PluginConfigResponse
        """
        # 查询现有配置
        result = await session.execute(
            select(PluginConfig).where(
                PluginConfig.tenant_id == tenant_id,
                PluginConfig.plugin_id == plugin_id,
            )
        )
        config = result.scalar_one_or_none()

        # 从插件定义获取完整声明信息
        from tenant.models.plugin import TenantPluginDefinition

        definition_result = await session.execute(
            select(TenantPluginDefinition).where(
                TenantPluginDefinition.plugin_id == plugin_id
            )
        )
        definition = definition_result.scalar_one_or_none()

        # 构建完整的插件配置
        full_plugin_config = {}
        if definition and definition.declaration:
            # 从声明中提取配置
            declaration = definition.declaration

            # 复制配置字段
            if "configuration" in declaration:
                full_plugin_config["configuration"] = declaration["configuration"]
            if "tools_configuration" in declaration:
                full_plugin_config["tools_configuration"] = declaration["tools_configuration"]
            if "models_configuration" in declaration:
                full_plugin_config["models_configuration"] = declaration["models_configuration"]
            if "agent_strategies_configuration" in declaration:
                full_plugin_config["agent_strategies_configuration"] = declaration["agent_strategies_configuration"]

        # 合并用户提供的凭证配置
        if plugin_config:
            full_plugin_config.update(plugin_config)

        if not config:
            # 创建新配置
            from framework.tenant.plugin_protocols import get_plugin_installation_provider

            provider = get_plugin_installation_provider()
            installation = await provider.get_installation(tenant_id, plugin_id)

            plugin_unique_identifier = (
                installation.plugin_unique_identifier
                if installation
                else f"{plugin_id}:latest"
            )

            config = PluginConfig(
                tenant_id=tenant_id,
                plugin_id=plugin_id,
                plugin_unique_identifier=plugin_unique_identifier,
                plugin_config=full_plugin_config,
                runtime_config=runtime_config,
            )
            session.add(config)
        else:
            # 更新现有配置：合并声明信息和凭证
            if config.plugin_config:
                # 保留现有的声明信息，更新凭证
                existing_config = config.plugin_config.copy()
                # 只更新凭证相关字段
                if plugin_config:
                    for key, value in plugin_config.items():
                        existing_config[key] = value
                    existing_config["validated"] = None
                config.plugin_config = existing_config
            else:
                config.plugin_config = full_plugin_config

            config.runtime_config = runtime_config

        await session.flush()

        _logger.info(f"插件配置已保存: {plugin_id}")

        return PluginConfigResponse(
            plugin_id=plugin_id,
            validated=config.plugin_config.get("validated") if config.plugin_config else None,
        )

    async def test_plugin(
        self,
        session: AsyncSession,
        tenant_id: str,
        plugin_id: str,
    ) -> PluginTestResponse:
        """
        测试插件配置连接

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginTestResponse
        """
        # 获取插件配置
        result = await session.execute(
            select(PluginConfig).where(
                PluginConfig.tenant_id == tenant_id,
                PluginConfig.plugin_id == plugin_id,
            )
        )
        config = result.scalar_one_or_none()

        if not config or not config.plugin_config:
            return PluginTestResponse(
                plugin_id=plugin_id,
                validated=False,
                message="插件未配置，请先配置插件",
            )

        try:
            # 调用插件管理器的实际测试连接接口
            from ai.components.plugin.engine.core.plugin_manager import (
                PluginManagerFactory,
            )

            manager = await PluginManagerFactory.get_manager(tenant_id, session)
            validated, message = await manager.test_plugin_connection(session, plugin_id)

            # 更新配置的验证状态
            config.plugin_config["validated"] = validated
            await session.flush()

            _logger.info(f"插件配置测试完成: {plugin_id}, 结果: {validated}")

            return PluginTestResponse(
                plugin_id=plugin_id,
                validated=validated,
                message=message,
            )
        except Exception as e:
            _logger.exception(f"插件配置测试失败: {plugin_id}")

            # 更新配置的验证状态为失败
            config.plugin_config["validated"] = False
            await session.flush()

            return PluginTestResponse(
                plugin_id=plugin_id,
                validated=False,
                message=f"连接失败: {str(e)}",
            )

    async def start_plugin(
        self,
        session: AsyncSession,
        tenant_id: str,
        plugin_id: str,
    ) -> PluginStartResponse:
        """
        启动插件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginStartResponse
        """
        # 检查配置是否存在
        result = await session.execute(
            select(PluginConfig).where(
                PluginConfig.tenant_id == tenant_id,
                PluginConfig.plugin_id == plugin_id,
            )
        )
        config = result.scalar_one_or_none()

        warning = None
        if not config:
            warning = "插件未配置，请先配置插件"
        elif not config.plugin_config:
            warning = "插件配置为空，可能无法正常工作"
        elif not config.plugin_config.get("validated"):
            warning = "配置未验证，可能无法正常工作"
        elif config.plugin_config.get("validated") is False:
            warning = "配置验证失败，可能无法正常工作"

        # 调用现有的启动方法
        try:
            response = await plugin_management_service.start_plugin_with_response(
                session, plugin_id
            )

            _logger.info(f"插件启动完成: {plugin_id}, 状态: {response.status}")

            return PluginStartResponse(
                plugin_id=plugin_id,
                status="ACTIVE" if response.success else "ERROR",
                port=response.port,
                warning=warning,
            )
        except Exception as e:
            _logger.exception(f"插件启动失败: {plugin_id}")

            return PluginStartResponse(
                plugin_id=plugin_id,
                status="ERROR",
                warning=str(e),
            )

    async def stop_plugin(
        self,
        session: AsyncSession,
        tenant_id: str,
        plugin_id: str,
    ) -> PluginStopResponse:
        """
        停止插件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginStopResponse
        """
        # 调用现有的停止方法
        try:
            response = await plugin_management_service.stop_plugin_with_response(
                session, plugin_id
            )

            _logger.info(f"插件停止完成: {plugin_id}, 状态: {response.status}")

            return PluginStopResponse(
                plugin_id=plugin_id,
                status="INACTIVE" if response.success else "ERROR",
            )
        except Exception as e:
            _logger.exception(f"插件停止失败: {plugin_id}")

            return PluginStopResponse(
                plugin_id=plugin_id,
                status="ERROR",
            )


# 单例实例
plugin_config_service = PluginConfigService()
