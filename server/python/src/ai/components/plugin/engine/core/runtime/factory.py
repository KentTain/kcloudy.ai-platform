"""
插件运行时工厂
使用工厂模式创建不同类型的运行时实例
"""

from pathlib import Path

from ai.components.plugin.engine.core.runtime.base import PluginRuntime
from ai.components.plugin.engine.core.runtime.local_runtime import LocalPluginRuntime
from ai.components.plugin.engine.models.enums import RuntimeType
from ai.components.plugin.engine.models.plugin import PluginInfo


class RuntimeFactory:
    """运行时工厂类"""

    def __init__(self):
        # 注册运行时类型映射
        self._runtime_classes: dict[str, type[PluginRuntime]] = {
            RuntimeType.LOCAL.value: LocalPluginRuntime,
        }

    async def create_runtime(
        self, plugin_info: PluginInfo, workspace_dir: Path
    ) -> PluginRuntime:
        """
        创建运行时实例

        Args:
            plugin_info: 插件信息
            workspace_dir: 工作目录

        Returns:
            运行时实例
        """
        # 从插件配置中获取运行时类型
        runtime_type = self._get_runtime_type(plugin_info)

        # 获取运行时类
        runtime_class = self._runtime_classes.get(runtime_type)
        if not runtime_class:
            raise ValueError(f"不支持的运行时类型: {runtime_type}")

        # 创建运行时实例
        runtime = runtime_class(plugin_info=plugin_info, workspace_dir=workspace_dir)

        return runtime

    def _get_runtime_type(self, plugin_info: PluginInfo) -> str:
        """
        从插件配置中获取运行时类型

        Args:
            plugin_info: 插件信息

        Returns:
            运行时类型
        """

        # 默认使用本地运行时
        return RuntimeType.LOCAL.value
