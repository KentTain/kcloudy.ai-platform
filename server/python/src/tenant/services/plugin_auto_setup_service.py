"""插件自动设置编排服务"""

from __future__ import annotations

from dataclasses import dataclass, field
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from framework.configs.plugin_auto_setup import PluginAutoSetupConfig, PluginAutoSetupItem
from framework.tenant.context import TenantContext
from framework.tenant.plugin_protocols import (
    get_plugin_config_provider,
    get_plugin_installation_provider,
)
from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.models.plugin_installation import TenantPluginInstallation

_logger = logger.bind(name=__name__)


@dataclass
class StartupSetupResult:
    """启动设置结果统计"""
    success_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    errors: list[str] = field(default_factory=list)


class PluginAutoSetupService:
    """插件自动设置编排服务"""

    async def setup_plugins(
        self,
        session: AsyncSession,
        config: PluginAutoSetupConfig,
    ) -> StartupSetupResult:
        """
        执行插件自动设置

        Args:
            session: 数据库会话
            config: 自动设置配置

        Returns:
            StartupSetupResult: 设置结果统计
        """
        result = StartupSetupResult()

        if not config.enabled:
            _logger.info("插件自动设置已禁用，跳过")
            return result

        for plugin_config in config.plugins:
            try:
                # 步骤1: 安装插件（幂等）
                installation = await self._install_plugin(session, plugin_config)

                if not installation:
                    result.skipped_count += 1
                    continue

                # 安装使用独立事务：提交后供后续配置/启动的 Provider 可见
                await session.commit()

                # 步骤2: 配置凭证
                if plugin_config.credentials:
                    await self._configure_credentials(
                        plugin_config.plugin_id,
                        plugin_config.credentials,
                    )

                # 步骤3: 启动插件
                if plugin_config.auto_start:
                    await self._start_plugin(plugin_config.plugin_id)

                result.success_count += 1
                _logger.info(f"插件自动设置成功: {plugin_config.plugin_id}")

            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{plugin_config.plugin_id}: {str(e)}")
                _logger.error(f"插件自动设置失败: {plugin_config.plugin_id}, {e}")

        return result

    async def _install_plugin(
        self,
        session: AsyncSession,
        config: PluginAutoSetupItem,
    ) -> TenantPluginInstallation | None:
        """
        安装插件（幂等）

        Args:
            session: 数据库会话
            config: 插件配置

        Returns:
            新建的安装记录；已安装时返回 None

        Raises:
            ValueError: 插件定义不存在
        """
        tenant_id = TenantContext.get_tenant_id()

        # 1. 检查是否已安装
        existing = await TenantPluginInstallation.first_by_fields(
            session,
            {"tenant_id": tenant_id, "plugin_id": config.plugin_id},
        )

        if existing:
            _logger.debug(f"插件已安装，跳过: {config.plugin_id}")
            return None

        # 2. 获取插件定义
        definition = await TenantPluginDefinition.one_by_field(
            session, "plugin_id", config.plugin_id
        )

        if not definition:
            raise ValueError(f"插件定义不存在: {config.plugin_id}")

        # 3. 创建安装记录
        installation = TenantPluginInstallation(
            tenant_id=tenant_id,
            plugin_id=config.plugin_id,
            plugin_unique_identifier=definition.plugin_unique_identifier,
            status="PENDING",
            auto_start=config.auto_start,
            plugin_type=definition.install_type,
        )
        session.add(installation)
        await session.flush()

        return installation

    async def _configure_credentials(
        self,
        plugin_id: str,
        credentials: dict[str, str],
    ) -> None:
        """
        配置插件凭证（通过 PluginConfigProvider 委托给 ai 模块）

        Args:
            plugin_id: 插件ID
            credentials: 凭证配置
        """
        tenant_id = TenantContext.get_tenant_id()

        provider = get_plugin_config_provider()
        await provider.configure_plugin(
            tenant_id=tenant_id,
            plugin_id=plugin_id,
            plugin_config=credentials,
            runtime_config=None,
        )

        _logger.info(f"插件凭证已配置: {plugin_id}")

    async def _start_plugin(self, plugin_id: str) -> None:
        """
        启动插件（通过 PluginInstallationProvider）

        Args:
            plugin_id: 插件ID
        """
        tenant_id = TenantContext.get_tenant_id()

        provider = get_plugin_installation_provider()
        await provider.start_installation(tenant_id, plugin_id)

        _logger.info(f"插件已启动: {plugin_id}")


# 单例实例
plugin_auto_setup_service = PluginAutoSetupService()
