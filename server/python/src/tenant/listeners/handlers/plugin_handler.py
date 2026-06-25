"""
插件安装/卸载事件处理器

处理 AI 模块发布的插件安装失败和卸载失败事件，
维护 Tenant 侧安装记录状态一致性。
"""

from loguru import logger

from framework.database.dependencies import get_task_session
from framework.events.domain_events import (
    PluginInstallationFailed,
    PluginUninstallFailed,
)
from tenant.models.plugin_installation import TenantPluginInstallation

_logger = logger.bind(name=__name__)


class PluginInstallationFailedHandler:
    """插件安装失败事件处理器"""

    async def handle(self, event: PluginInstallationFailed) -> None:
        """
        处理安装失败事件

        将 Tenant 侧安装记录状态更新为 FAILED。

        Args:
            event: 插件安装失败事件
        """
        async with get_task_session() as session:
            installation = await TenantPluginInstallation.first_by_fields(
                session,
                {
                    "tenant_id": event.tenant_id,
                    "plugin_id": event.plugin_id,
                },
            )
            if installation:
                installation.status = "FAILED"
                await session.flush()
                _logger.info(
                    f"插件安装记录已标记为 FAILED: "
                    f"tenant_id={event.tenant_id}, plugin_id={event.plugin_id}"
                )
            else:
                _logger.warning(
                    f"插件安装记录不存在，无法更新状态: "
                    f"tenant_id={event.tenant_id}, plugin_id={event.plugin_id}"
                )


class PluginUninstallFailedHandler:
    """插件卸载失败事件处理器"""

    async def handle(self, event: PluginUninstallFailed) -> None:
        """
        处理卸载失败事件

        Tenant 侧记录已删除，仅记录失败日志供审计。

        Args:
            event: 插件卸载失败事件
        """
        _logger.error(
            f"插件卸载失败: tenant_id={event.tenant_id}, "
            f"plugin_id={event.plugin_id}, "
            f"error={event.error_message}"
        )
