"""
插件运行时工厂
使用工厂模式创建不同类型的运行时实例
"""

from pathlib import Path

from ai.components.plugin.engine.core.runtime.base import PluginRuntime
from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
    KnowledgeSkillRuntime,
)
from ai.components.plugin.engine.core.runtime.local_runtime import LocalPluginRuntime
from ai.components.plugin.engine.core.runtime.sandbox_skill_runtime import (
    SandboxSkillRuntime,
)
from ai.components.plugin.engine.models.enums import RuntimeType
from ai.components.plugin.engine.models.plugin import PluginInfo


class RuntimeFactory:
    """运行时工厂类"""

    def __init__(self):
        # 注册运行时类型映射
        self._runtime_classes: dict[str, type[PluginRuntime]] = {
            RuntimeType.LOCAL.value: LocalPluginRuntime,
            RuntimeType.SANDBOX.value: SandboxSkillRuntime,
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
        # Skill 类型路由
        if self._is_skill_plugin(plugin_info):
            return self._create_skill_runtime(plugin_info, workspace_dir)

        # 从插件配置中获取运行时类型
        runtime_type = self._get_runtime_type(plugin_info)

        # 获取运行时类
        runtime_class = self._runtime_classes.get(runtime_type)
        if not runtime_class:
            raise ValueError(f"不支持的运行时类型: {runtime_type}")

        # 创建运行时实例
        runtime = runtime_class(plugin_info=plugin_info, workspace_dir=workspace_dir)

        return runtime

    def _is_skill_plugin(self, plugin_info: PluginInfo) -> bool:
        """
        判断是否为 Skill 类型插件

        Args:
            plugin_info: 插件信息

        Returns:
            是否为 Skill 类型插件
        """
        if not plugin_info.config or not plugin_info.config.configuration:
            return False

        # 通过检查 plugins 扩展配置中是否有 skill 配置来判断
        # Note: 当前 PluginType 只有 Plugin，Skill 类型通过其他方式判断
        # TODO: 后续根据 Skill 功能完善判断逻辑
        plugins = plugin_info.config.configuration.plugins
        if plugins:
            # 检查是否有 skill 相关的扩展配置
            return hasattr(plugins, 'skills') and bool(plugins.skills)

        return False

    def _create_skill_runtime(
        self, plugin_info: PluginInfo, workspace_dir: Path
    ) -> PluginRuntime:
        """
        创建 Skill 运行时实例

        Args:
            plugin_info: 插件信息
            workspace_dir: 工作目录

        Returns:
            Skill 运行时实例

        Raises:
            ValueError: 不支持的 Skill 类型
        """
        # 从 declaration 中获取 skill_type，未配置时默认 knowledge
        configuration = plugin_info.config.configuration
        declaration = getattr(configuration, "declaration", None) or {}
        skill_config = declaration.get("skill", {}) if isinstance(declaration, dict) else {}
        skill_type = (
            skill_config.get("skill_type", "knowledge")
            if isinstance(skill_config, dict)
            else "knowledge"
        )

        if skill_type == "knowledge":
            return KnowledgeSkillRuntime(plugin_info, workspace_dir)
        elif skill_type == "script":
            return SandboxSkillRuntime(plugin_info, workspace_dir)
        else:
            raise ValueError(f"不支持的 Skill 类型: {skill_type}")

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
