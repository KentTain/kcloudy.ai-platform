"""
插件安装任务执行器

从 Redis Stream 消费安装任务，下载插件包后委托给统一安装编排。
"""

from __future__ import annotations

import logging
from typing import Any

from ai.components.plugin.engine.models.request import InstallRequest
from ai.services.plugin import install_task_service
from framework.database.dependencies import get_task_session
from framework.events.domain_events import PluginInstallationFailed
from framework.events.publisher import get_event_publisher
from framework.tenant.context import TenantContext
from tenant.services.plugin import plugin_storage_service

_logger = logging.getLogger(__name__)


class InstallTaskExecutor:
    """插件安装任务执行器

    从 MinIO 下载插件包，获取 TenantPluginManager，
    委托给 _execute_installation() 统一编排完成安装。
    """

    async def execute(self, task_data: dict[str, Any]) -> None:
        """
        执行安装任务

        Args:
            task_data: 任务数据
                - task_id: 任务ID
                - tenant_id: 租户ID
                - plugin_id: 插件ID
                - plugin_unique_identifier: 插件唯一标识符
                - auto_start: 是否自动启动
        """
        task_id = task_data.get("task_id")
        tenant_id = task_data.get("tenant_id")
        plugin_id = task_data.get("plugin_id")
        plugin_unique_identifier = task_data.get("plugin_unique_identifier")
        auto_start = task_data.get("auto_start", True)

        if not all([task_id, tenant_id, plugin_id]):
            _logger.error(f"任务数据不完整: {task_data}")
            return

        # 设置租户上下文
        TenantContext.set_tenant_id(tenant_id)

        async with get_task_session() as session:
            try:
                # 更新任务状态为 running
                await install_task_service.update_task_status(
                    session,
                    task_id,
                    status="running",
                    progress=5,
                    current_step="开始安装",
                )

                # Step 1: 从 MinIO 下载插件包
                await install_task_service.update_task_step(
                    session, task_id, step_name="download",
                    step_status="running", progress=10,
                )

                package_data = await plugin_storage_service.download_package(
                    plugin_id=plugin_id,
                    version=self._extract_version(plugin_unique_identifier),
                )
                if not package_data:
                    raise RuntimeError(f"插件包不存在: {plugin_id}")

                await install_task_service.update_task_step(
                    session, task_id, step_name="download",
                    step_status="completed", progress=25,
                )

                # Step 2: 获取 PluginManager 并调用统一安装编排
                await install_task_service.update_task_step(
                    session, task_id, step_name="install",
                    step_status="running", progress=30,
                )

                from ai.components.plugin.engine.core.plugin_manager import (
                    PluginManagerFactory,
                )

                plugin_manager = await PluginManagerFactory.get_manager(
                    tenant_id, session
                )
                install_request = InstallRequest(auto_start=auto_start)
                await plugin_manager.install_plugin(
                    session,
                    plugin_package=package_data,
                    install_request=install_request,
                )

                await install_task_service.update_task_step(
                    session, task_id, step_name="install",
                    step_status="completed", progress=90,
                )

                # Step 3: 完成安装
                await install_task_service.update_task_status(
                    session, task_id,
                    status="completed", progress=100,
                    current_step="安装完成",
                )

                _logger.info(f"安装任务完成: task_id={task_id}, plugin_id={plugin_id}")

            except Exception as e:
                _logger.exception(f"安装任务执行失败: task_id={task_id}, error={e}")

                # 更新任务状态为 failed
                await install_task_service.update_task_status(
                    session, task_id,
                    status="failed", progress=0,
                    error_message=str(e),
                )

                # 发布安装失败事件
                await self._publish_installation_failed_event(
                    tenant_id, plugin_id, str(e)
                )

    async def _publish_installation_failed_event(
        self,
        tenant_id: str,
        plugin_id: str,
        error_message: str,
    ) -> None:
        """发布安装失败事件"""
        try:
            publisher = get_event_publisher()
            event = PluginInstallationFailed(
                tenant_id=tenant_id,
                plugin_id=plugin_id,
                error_message=error_message,
            )
            await publisher.publish(event)
            _logger.info(f"已发布安装失败事件: tenant_id={tenant_id}, plugin_id={plugin_id}")
        except Exception as e:
            _logger.error(f"发布安装失败事件失败: {e}")

    def _extract_version(self, plugin_unique_identifier: str) -> str:
        """从 plugin_unique_identifier 中提取版本号

        格式: {plugin_id}:{version}@{checksum}
        示例: author/plugin:1.0.0@abc123
        """
        try:
            parts = plugin_unique_identifier.split(":")
            if len(parts) >= 2:
                version_part = parts[1]
                if "@" in version_part:
                    return version_part.split("@")[0]
                return version_part
            return "latest"
        except Exception:
            return "latest"
