"""插件验证服务"""

from __future__ import annotations

import asyncio
from loguru import logger

from ai.services.plugin_config_service import plugin_config_service
from framework.configs.plugin_auto_setup import VerificationConfig
from framework.database.dependencies import get_task_session
from framework.tenant.context import TenantContext

_logger = logger.bind(name=__name__)


class PluginVerificationService:
    """插件验证服务"""

    async def verify_all_plugins(
        self,
        plugin_ids: list[str],
        config: VerificationConfig,
    ) -> dict[str, bool]:
        """
        并发验证所有插件

        Args:
            plugin_ids: 插件ID列表
            config: 验证配置

        Returns:
            dict[plugin_id, is_valid]: 验证结果
        """
        if not plugin_ids:
            return {}

        tasks = [
            self._verify_single_plugin(plugin_id, config.timeout)
            for plugin_id in plugin_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            plugin_id: result if isinstance(result, bool) else False
            for plugin_id, result in zip(plugin_ids, results)
        }

    async def _verify_single_plugin(
        self,
        plugin_id: str,
        timeout: int,
    ) -> bool:
        """
        验证单个插件（通过 plugin_config_service.test_plugin）

        Args:
            plugin_id: 插件ID
            timeout: 超时时间(秒)

        Returns:
            bool: 是否验证通过
        """
        try:
            async with get_task_session() as session:
                tenant_id = TenantContext.get_tenant_id()
                response = await asyncio.wait_for(
                    plugin_config_service.test_plugin(
                        session, tenant_id, plugin_id
                    ),
                    timeout=timeout,
                )
                return response.validated
        except asyncio.TimeoutError:
            _logger.warning(f"插件验证超时: {plugin_id}")
            return False
        except Exception as e:
            _logger.warning(f"插件验证失败: {plugin_id}, {e}")
            return False

    async def handle_verification_failure(
        self,
        plugin_id: str,
        strategy: str,
    ) -> None:
        """
        处理验证失败

        Args:
            plugin_id: 插件ID
            strategy: 失败策略 (warn/degrade/fail)
        """
        if strategy == "warn":
            _logger.warning(f"插件验证失败: {plugin_id}")
        elif strategy == "degrade":
            await self._update_runtime_state(plugin_id, "DEGRADED")
            _logger.warning(f"插件已降级: {plugin_id}")
        elif strategy == "fail":
            _logger.error(f"插件验证失败: {plugin_id}")

    async def _update_runtime_state(
        self,
        plugin_id: str,
        state: str,
    ) -> None:
        """
        更新插件运行时状态

        Args:
            plugin_id: 插件ID
            state: 状态
        """
        # TODO: 实现运行时状态更新
        _logger.info(f"更新插件状态: {plugin_id} -> {state}")


# 单例实例
plugin_verification_service = PluginVerificationService()
