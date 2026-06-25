"""
插件安装/卸载事件处理器

处理 AI 模块发布的插件安装失败和卸载失败事件，
维护 Tenant 侧安装记录状态一致性。
"""

import json
import logging
from typing import Any

from framework.database.dependencies import get_listener_session
from framework.events.base import EventStream
from framework.tenant.context import TenantContext
from tenant.models.plugin_installation import TenantPluginInstallation

_logger = logging.getLogger(__name__)


class PluginInstallationFailedHandler:
    """插件安装失败事件处理器"""

    stream = EventStream.PLUGIN_INSTALLATION_FAILED

    async def handle(self, message: dict[str, Any]) -> None:
        """
        处理安装失败事件

        将 Tenant 侧安装记录状态更新为 FAILED。

        Args:
            message: 消息内容
        """
        try:
            data = json.loads(message.get("data", "{}"))
            tenant_id = data.get("tenant_id")
            plugin_id = data.get("plugin_id")

            if not tenant_id or not plugin_id:
                _logger.warning(f"PluginInstallationFailed 事件缺少必要字段: {data}")
                return

            _logger.info(
                f"处理 PluginInstallationFailed 事件: "
                f"tenant_id={tenant_id}, plugin_id={plugin_id}"
            )

            # 设置租户上下文
            TenantContext.set_tenant_id(tenant_id)

            async with get_listener_session() as session:
                installation = await TenantPluginInstallation.first_by_fields(
                    session,
                    {
                        "tenant_id": tenant_id,
                        "plugin_id": plugin_id,
                    },
                )
                if installation:
                    installation.status = "FAILED"
                    await session.flush()
                    _logger.info(
                        f"插件安装记录已标记为 FAILED: "
                        f"tenant_id={tenant_id}, plugin_id={plugin_id}"
                    )
                else:
                    _logger.warning(
                        f"插件安装记录不存在，无法更新状态: "
                        f"tenant_id={tenant_id}, plugin_id={plugin_id}"
                    )

        except Exception as e:
            _logger.exception(f"处理 PluginInstallationFailed 事件失败: {e}")
            raise


class PluginUninstallFailedHandler:
    """插件卸载失败事件处理器"""

    stream = EventStream.PLUGIN_UNINSTALL_FAILED

    async def handle(self, message: dict[str, Any]) -> None:
        """
        处理卸载失败事件

        Tenant 侧记录已删除，仅记录失败日志供审计。

        Args:
            message: 消息内容
        """
        try:
            data = json.loads(message.get("data", "{}"))
            tenant_id = data.get("tenant_id")
            plugin_id = data.get("plugin_id")
            error_message = data.get("error_message", "")

            if not tenant_id or not plugin_id:
                _logger.warning(f"PluginUninstallFailed 事件缺少必要字段: {data}")
                return

            _logger.error(
                f"插件卸载失败: tenant_id={tenant_id}, "
                f"plugin_id={plugin_id}, "
                f"error={error_message}"
            )

        except Exception as e:
            _logger.exception(f"处理 PluginUninstallFailed 事件失败: {e}")
            raise
