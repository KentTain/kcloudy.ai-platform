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
                # 步骤1: 安装插件（当 auto_install=True 时执行，幂等）
                if plugin_config.auto_install:
                    newly_installed = await self._install_plugin(session, plugin_config)

                    if newly_installed:
                        # 新安装：提交事务使安装记录对后续 Provider 可见
                        await session.commit()
                    else:
                        result.skipped_count += 1

                # 步骤2: 配置凭证（始终执行，幂等更新）
                if plugin_config.credentials:
                    await self._configure_credentials(
                        plugin_config.plugin_id,
                        plugin_config.credentials,
                    )

                # 步骤3: 启动插件（当 auto_start=True 时执行，幂等）
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
    ) -> bool:
        """
        安装插件（幂等）

        Args:
            session: 数据库会话
            config: 插件配置

        Returns:
            是否新安装（已安装返回 False）

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
            _logger.debug(f"插件已安装，跳过安装步骤: {config.plugin_id}")
            return False

        # 2. 获取插件定义
        definition = await TenantPluginDefinition.one_by_field(
            session, "plugin_id", config.plugin_id
        )

        if not definition:
            raise ValueError(f"插件定义不存在: {config.plugin_id}")

        # 3. 从 MinIO 下载插件包并调用 PluginManager 安装
        # 注意：这里直接调用 AI 模块的 PluginManager，违反了模块间依赖规则。
        # 这是一个过渡期的实现，未来应该通过 Inner API 或事件机制解耦。
        from ai.components.plugin.engine.core.plugin_manager import PluginManagerFactory
        from tenant.services.plugin_storage_service import plugin_storage_service

        # 从 plugin_unique_identifier 解析版本号
        # 支持两种格式：
        # 1. {plugin_id}:{version}@{checksum} - 完整格式
        # 2. {plugin_id}@{version} - 简化格式
        identifier = definition.plugin_unique_identifier

        # 尝试格式1: {plugin_id}:{version}@{checksum}
        if ":" in identifier:
            # 格式: {plugin_id}:{version}@{checksum}
            parts = identifier.split(":")
            if len(parts) >= 2:
                version_part = parts[1].split("@")[0]  # 提取版本号
            else:
                raise ValueError(f"无效的插件唯一标识符: {identifier}")
        elif "@" in identifier:
            # 格式: {plugin_id}@{version}
            parts = identifier.split("@")
            if len(parts) >= 2:
                version_part = parts[1]  # 直接取版本号
            else:
                raise ValueError(f"无效的插件唯一标识符: {identifier}")
        else:
            # 无法解析，使用默认值
            version_part = "latest"
            _logger.warning(f"无法解析插件版本，使用默认值: {identifier}")

        try:
            # 下载插件包
            package_data = await plugin_storage_service.download_package(
                config.plugin_id, version_part
            )
            _logger.info(f"从 MinIO 下载插件包成功: {config.plugin_id}:{version_part}")

            # 获取插件管理器
            manager = await PluginManagerFactory.get_manager(tenant_id, session)

            # 调用 PluginManager.install_plugin 安装插件
            await manager.install_plugin(
                session=session,
                plugin_package=package_data,
                install_request=None,  # 无需安装请求，插件定义已经存在
            )

            _logger.info(f"插件安装成功: {config.plugin_id}")
            return True

        except Exception as e:
            _logger.error(f"插件安装失败: {config.plugin_id}, 错误: {e}")
            raise

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
