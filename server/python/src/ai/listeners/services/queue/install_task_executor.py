"""
插件安装任务执行器

执行实际的插件安装逻辑：下载插件包、校验、安装、初始化配置。
"""

from __future__ import annotations

import logging
from typing import Any

from ai.models.plugin_config import PluginConfig as AIPluginConfig
from ai.models.plugin_runtime_state import PluginRuntimeState
from ai.services.install_task_service import install_task_service
from framework.database.dependencies import get_task_session
from framework.events.domain_events import PluginInstallationFailed
from framework.events.publisher import get_event_publisher
from framework.tenant.plugin_protocols import get_plugin_installation_provider
from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.models.plugin_installation import TenantPluginInstallation
from tenant.services.plugin_storage_service import plugin_storage_service

_logger = logging.getLogger(__name__)


class InstallTaskExecutor:
    """插件安装任务执行器"""

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

                # Step 1: 下载插件包 (5-25%)
                await self._download_package(
                    session, task_id, plugin_id, plugin_unique_identifier
                )

                # Step 2: 校验插件包 (25-35%)
                await self._validate_package(
                    session, task_id, plugin_id, plugin_unique_identifier
                )

                # Step 3: 创建 AI 侧配置 (35-55%)
                await self._create_ai_config(
                    session, task_id, tenant_id, plugin_id, plugin_unique_identifier
                )

                # Step 4: 更新安装记录状态 (55-75%)
                await self._update_installation_status(
                    session, task_id, tenant_id, plugin_id
                )

                # Step 5: 完成安装 (75-100%)
                await self._finalize_installation(
                    session, task_id, tenant_id, plugin_id, auto_start
                )

                _logger.info(f"安装任务完成: task_id={task_id}, plugin_id={plugin_id}")

            except Exception as e:
                _logger.exception(f"安装任务执行失败: task_id={task_id}, error={e}")

                # 更新任务状态为 failed
                await install_task_service.update_task_status(
                    session,
                    task_id,
                    status="failed",
                    progress=0,
                    error_message=str(e),
                )

                # 发布安装失败事件
                await self._publish_installation_failed_event(
                    tenant_id, plugin_id, str(e)
                )

    async def _download_package(
        self,
        session,
        task_id: str,
        plugin_id: str,
        plugin_unique_identifier: str,
    ) -> None:
        """下载插件包"""
        await install_task_service.update_task_step(
            session,
            task_id,
            step_name="download",
            step_status="running",
            progress=10,
        )

        try:
            # 从 MinIO 下载插件包
            # 注意：实际安装时可能需要解压到本地目录
            # 这里只是检查插件包是否存在
            package_data = await plugin_storage_service.download_plugin_package(
                plugin_id=plugin_id,
                # 从 plugin_unique_identifier 中提取版本
                version=self._extract_version(plugin_unique_identifier),
            )

            if not package_data:
                raise RuntimeError(f"插件包不存在: {plugin_id}")

            await install_task_service.update_task_step(
                session,
                task_id,
                step_name="download",
                step_status="completed",
                progress=25,
            )

        except Exception as e:
            await install_task_service.update_task_step(
                session,
                task_id,
                step_name="download",
                step_status="failed",
                progress=0,
            )
            raise RuntimeError(f"下载插件包失败: {e}")

    async def _validate_package(
        self,
        session,
        task_id: str,
        plugin_id: str,
        plugin_unique_identifier: str,
    ) -> None:
        """校验插件包"""
        await install_task_service.update_task_step(
            session,
            task_id,
            step_name="validate",
            step_status="running",
            progress=30,
        )

        try:
            # 校验逻辑（可以扩展：校验签名、校验和等）
            # 这里暂时跳过详细校验

            await install_task_service.update_task_step(
                session,
                task_id,
                step_name="validate",
                step_status="completed",
                progress=35,
            )

        except Exception as e:
            await install_task_service.update_task_step(
                session,
                task_id,
                step_name="validate",
                step_status="failed",
                progress=0,
            )
            raise RuntimeError(f"校验插件包失败: {e}")

    async def _create_ai_config(
        self,
        session,
        task_id: str,
        tenant_id: str,
        plugin_id: str,
        plugin_unique_identifier: str,
    ) -> None:
        """创建 AI 侧配置"""
        await install_task_service.update_task_step(
            session,
            task_id,
            step_name="install",
            step_status="running",
            progress=40,
        )

        try:
            # 获取插件定义
            from sqlalchemy import select

            stmt = select(TenantPluginDefinition).where(
                TenantPluginDefinition.plugin_id == plugin_id
            )
            result = await session.execute(stmt)
            definition = result.scalar_one_or_none()

            if not definition:
                raise RuntimeError(f"插件定义不存在: {plugin_id}")

            # 创建 AI 侧配置
            existing_config = await AIPluginConfig.one_by_fields(
                session,
                {"tenant_id": tenant_id, "plugin_id": plugin_id},
            )

            if not existing_config:
                ai_config = AIPluginConfig(
                    tenant_id=tenant_id,
                    plugin_id=plugin_id,
                    plugin_config=definition.declaration,
                    runtime_config={},
                )
                session.add(ai_config)
                await session.flush()

            # 创建运行时状态
            existing_state = await PluginRuntimeState.one_by_fields(
                session,
                {"tenant_id": tenant_id, "plugin_id": plugin_id},
            )

            if not existing_state:
                runtime_state = PluginRuntimeState(
                    tenant_id=tenant_id,
                    plugin_id=plugin_id,
                    status="inactive",
                    call_count=0,
                    error_count=0,
                )
                session.add(runtime_state)
                await session.flush()

            await install_task_service.update_task_step(
                session,
                task_id,
                step_name="install",
                step_status="completed",
                progress=55,
            )

        except Exception as e:
            await install_task_service.update_task_step(
                session,
                task_id,
                step_name="install",
                step_status="failed",
                progress=0,
            )
            raise RuntimeError(f"创建 AI 配置失败: {e}")

    async def _update_installation_status(
        self,
        session,
        task_id: str,
        tenant_id: str,
        plugin_id: str,
    ) -> None:
        """更新安装记录状态"""
        await install_task_service.update_task_step(
            session,
            task_id,
            step_name="configure",
            step_status="running",
            progress=60,
        )

        try:
            # 更新 Tenant 侧安装记录状态为 ACTIVE
            provider = get_plugin_installation_provider()
            await provider.update_installation(
                tenant_id,
                plugin_id,
                {"status": "ACTIVE"},
            )

            await install_task_service.update_task_step(
                session,
                task_id,
                step_name="configure",
                step_status="completed",
                progress=75,
            )

        except Exception as e:
            await install_task_service.update_task_step(
                session,
                task_id,
                step_name="configure",
                step_status="failed",
                progress=0,
            )
            raise RuntimeError(f"更新安装状态失败: {e}")

    async def _finalize_installation(
        self,
        session,
        task_id: str,
        tenant_id: str,
        plugin_id: str,
        auto_start: bool,
    ) -> None:
        """完成安装"""
        await install_task_service.update_task_step(
            session,
            task_id,
            step_name="finalize",
            step_status="running",
            progress=80,
        )

        try:
            # 如果需要自动启动，可以在这里启动插件
            # 注意：启动插件需要插件管理器，这里暂时跳过

            # 更新任务状态为 completed
            await install_task_service.update_task_status(
                session,
                task_id,
                status="completed",
                progress=100,
                current_step="安装完成",
            )

            await install_task_service.update_task_step(
                session,
                task_id,
                step_name="finalize",
                step_status="completed",
                progress=100,
            )

        except Exception as e:
            await install_task_service.update_task_step(
                session,
                task_id,
                step_name="finalize",
                step_status="failed",
                progress=0,
            )
            raise RuntimeError(f"完成安装失败: {e}")

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
            # 格式: plugin_id:version@checksum
            parts = plugin_unique_identifier.split(":")
            if len(parts) >= 2:
                version_part = parts[1]
                # 移除 checksum 部分
                if "@" in version_part:
                    return version_part.split("@")[0]
                return version_part
            return "latest"
        except Exception:
            return "latest"
