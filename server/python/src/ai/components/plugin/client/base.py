from ai.components.plugin.engine.core.plugin_manager import (
    PluginManagerFactory,
    TenantPluginManager,
)


class BasePluginClient:
    async def _get_plugin_manager(self, tenant_id: str) -> TenantPluginManager:
        plugin_manager: TenantPluginManager = await PluginManagerFactory.get_manager(
            tenant_id
        )
        # 确保插件管理器已初始化
        if not plugin_manager._initialized:
            await plugin_manager.initialize()
        return plugin_manager

    def _extract_result_data(self, result: dict) -> dict:
        """
        从插件响应中提取实际的结果数据

        插件可能返回格式如: {'type': 'stream', 'data': {...}} 或直接返回数据

        Args:
            result: 插件返回的原始结果

        Returns:
            提取的实际数据
        """
        if isinstance(result, dict):
            # 检查是否是包装格式
            if "type" in result and "data" in result:
                # 对于stream类型，返回data字段的内容
                if result["type"] == "stream":
                    return result["data"]
                return result["data"]
            # 直接返回原始数据
            raise ValueError(f"插件返回的数据格式不正确: {result}")
