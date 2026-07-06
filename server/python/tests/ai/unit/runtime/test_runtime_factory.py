"""运行时工厂单元测试"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai.components.plugin.engine.models.plugin import PluginInfo


class TestRuntimeFactory:
    """运行时工厂测试"""

    @pytest.fixture
    def plugin_info_knowledge(self):
        """创建 Knowledge Skill 插件信息"""
        plugin_info = MagicMock(spec=PluginInfo)
        plugin_info.id = "test-author/test-knowledge-skill"
        plugin_info.name = "test-knowledge-skill"
        plugin_info.version = "1.0.0"

        # 创建配置对象，包含 skill declaration
        mock_config = MagicMock()
        mock_configuration = MagicMock()
        mock_configuration.author = "test-author"
        mock_configuration.name = "test-knowledge-skill"
        mock_configuration.version = "1.0.0"
        # 设置 declaration，包含 skill 配置
        mock_configuration.declaration = {
            "skill": {
                "skill_type": "knowledge",
                "description": "Test knowledge skill",
            }
        }
        mock_config.configuration = mock_configuration
        plugin_info.config = mock_config

        return plugin_info

    @pytest.fixture
    def plugin_info_sandbox(self):
        """创建 Sandbox Skill 插件信息"""
        plugin_info = MagicMock(spec=PluginInfo)
        plugin_info.id = "test-author/test-sandbox-skill"
        plugin_info.name = "test-sandbox-skill"
        plugin_info.version = "1.0.0"

        # 创建配置对象，包含 skill declaration
        mock_config = MagicMock()
        mock_configuration = MagicMock()
        mock_configuration.author = "test-author"
        mock_configuration.name = "test-sandbox-skill"
        mock_configuration.version = "1.0.0"
        # 设置 declaration，包含 skill 配置
        mock_configuration.declaration = {
            "skill": {
                "skill_type": "script",
                "description": "Test sandbox skill",
            }
        }
        mock_config.configuration = mock_configuration
        plugin_info.config = mock_config

        # 设置 runtime_config
        mock_runtime_config = MagicMock()
        mock_runtime_config.config = {
            "script_path": "main.py",
            "allowed_imports": ["json", "re"],
            "timeout": 30,
            "memory_limit_mb": 128,
        }
        plugin_info.config.runtime_config = mock_runtime_config

        return plugin_info

    @pytest.fixture
    def plugin_info_unknown_skill(self):
        """创建未知类型 Skill 插件信息"""
        plugin_info = MagicMock(spec=PluginInfo)
        plugin_info.id = "test-author/test-unknown-skill"
        plugin_info.name = "test-unknown-skill"
        plugin_info.version = "1.0.0"

        # 创建配置对象，包含未知 skill 类型
        mock_config = MagicMock()
        mock_configuration = MagicMock()
        mock_configuration.author = "test-author"
        mock_configuration.name = "test-unknown-skill"
        mock_configuration.version = "1.0.0"
        # 设置 declaration，包含未知 skill 类型
        mock_configuration.declaration = {
            "skill": {
                "skill_type": "unknown_type",
                "description": "Test unknown skill type",
            }
        }
        mock_config.configuration = mock_configuration
        plugin_info.config = mock_config

        return plugin_info

    @pytest.fixture
    def workspace_dir(self, tmp_path):
        """创建临时工作目录"""
        return tmp_path / "workspace"

    @pytest.mark.asyncio
    async def test_create_knowledge_skill_runtime(
        self, plugin_info_knowledge, workspace_dir
    ):
        """测试创建 KnowledgeSkillRuntime"""
        from ai.components.plugin.engine.core.runtime.factory import RuntimeFactory
        from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
            KnowledgeSkillRuntime,
        )

        factory = RuntimeFactory()
        runtime = await factory.create_runtime(plugin_info_knowledge, workspace_dir)

        assert isinstance(runtime, KnowledgeSkillRuntime)
        assert runtime.skill_type == "knowledge"
        assert runtime.plugin_id == "test-author/test-knowledge-skill"

    @pytest.mark.asyncio
    async def test_create_sandbox_skill_runtime(self, plugin_info_sandbox, workspace_dir):
        """测试创建 SandboxSkillRuntime"""
        from ai.components.plugin.engine.core.runtime.factory import RuntimeFactory
        from ai.components.plugin.engine.core.runtime.sandbox_skill_runtime import (
            SandboxSkillRuntime,
        )

        factory = RuntimeFactory()
        runtime = await factory.create_runtime(plugin_info_sandbox, workspace_dir)

        assert isinstance(runtime, SandboxSkillRuntime)
        assert runtime.skill_type == "script"
        assert runtime.plugin_id == "test-author/test-sandbox-skill"

    @pytest.mark.asyncio
    async def test_create_runtime_unknown_skill_type(
        self, plugin_info_unknown_skill, workspace_dir
    ):
        """测试未知 Skill 类型抛出 ValueError"""
        from ai.components.plugin.engine.core.runtime.factory import RuntimeFactory

        factory = RuntimeFactory()

        with pytest.raises(ValueError) as exc_info:
            await factory.create_runtime(plugin_info_unknown_skill, workspace_dir)

        assert "不支持的 Skill 类型" in str(exc_info.value)
