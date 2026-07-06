"""Knowledge Skill Runtime 单元测试"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.components.plugin.engine.core.exceptions import SkillPreparationError
from ai.components.plugin.engine.models.plugin import PluginInfo


class TestKnowledgeSkillRuntime:
    """Knowledge Skill Runtime 测试"""

    @pytest.fixture
    def plugin_info(self):
        """创建测试插件信息"""
        # 创建一个模拟的 PluginInfo，绕过 Pydantic 验证
        from unittest.mock import MagicMock
        from ai.components.plugin.engine.models.plugin import PluginInfo

        plugin_info = MagicMock(spec=PluginInfo)
        plugin_info.id = "test-author/test-skill"
        plugin_info.name = "test-skill"
        plugin_info.version = "1.0.0"

        # 创建一个模拟的 config 对象
        mock_config = MagicMock()
        mock_configuration = MagicMock()
        mock_configuration.author = "test-author"
        mock_configuration.name = "test-skill"
        mock_configuration.version = "1.0.0"
        mock_config.configuration = mock_configuration
        plugin_info.config = mock_config

        return plugin_info

    @pytest.fixture
    def workspace_dir(self, tmp_path):
        """创建临时工作目录"""
        return tmp_path / "workspace"

    def test_runtime_type(self, plugin_info, workspace_dir):
        """测试运行时类型"""
        from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
            KnowledgeSkillRuntime,
        )

        runtime = KnowledgeSkillRuntime(plugin_info, workspace_dir)

        assert runtime.skill_type == "knowledge"
        assert runtime.runtime_type == "none"

    @pytest.mark.asyncio
    async def test_prepare_success(self, plugin_info, workspace_dir):
        """测试成功准备"""
        from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
            KnowledgeSkillRuntime,
        )

        runtime = KnowledgeSkillRuntime(plugin_info, workspace_dir)

        # Mock PluginStorageService
        with patch(
            "ai.components.plugin.engine.core.runtime.knowledge_skill_runtime.plugin_storage_service"
        ) as mock_storage:
            mock_storage.load_skill_documents = AsyncMock(
                return_value={
                    "SKILL.md": "# Test Skill\n\nThis is a test skill.",
                    "EXAMPLES.md": "## Examples\n\nExample content.",
                }
            )

            await runtime.prepare()

            assert runtime.is_prepared
            assert "SKILL.md" in runtime._skill_documents

    @pytest.mark.asyncio
    async def test_prepare_missing_skill_md(self, plugin_info, workspace_dir):
        """测试缺少 SKILL.md 时抛出异常"""
        from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
            KnowledgeSkillRuntime,
        )

        runtime = KnowledgeSkillRuntime(plugin_info, workspace_dir)

        # Mock PluginStorageService
        with patch(
            "ai.components.plugin.engine.core.runtime.knowledge_skill_runtime.plugin_storage_service"
        ) as mock_storage:
            mock_storage.load_skill_documents = AsyncMock(
                return_value={
                    "README.md": "# README",
                }
            )

            with pytest.raises(SkillPreparationError) as exc_info:
                await runtime.prepare()

            assert "缺少 SKILL.md" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_prepare_strips_yaml_front_matter(self, plugin_info, workspace_dir):
        """测试移除 YAML front matter"""
        from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
            KnowledgeSkillRuntime,
        )

        runtime = KnowledgeSkillRuntime(plugin_info, workspace_dir)

        skill_md_with_yaml = """---
name: test-skill
version: 1.0.0
---

# Test Skill

This is the actual content.
"""

        # Mock PluginStorageService
        with patch(
            "ai.components.plugin.engine.core.runtime.knowledge_skill_runtime.plugin_storage_service"
        ) as mock_storage:
            mock_storage.load_skill_documents = AsyncMock(
                return_value={
                    "SKILL.md": skill_md_with_yaml,
                }
            )

            await runtime.prepare()

            assert "---" not in runtime._skill_documents["SKILL.md"]
            assert "# Test Skill" in runtime._skill_documents["SKILL.md"]

    @pytest.mark.asyncio
    async def test_invoke_stream_success(self, plugin_info, workspace_dir):
        """测试流式调用成功"""
        from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
            KnowledgeSkillRuntime,
        )

        runtime = KnowledgeSkillRuntime(plugin_info, workspace_dir)

        # Mock PluginStorageService
        with patch(
            "ai.components.plugin.engine.core.runtime.knowledge_skill_runtime.plugin_storage_service"
        ) as mock_storage:
            mock_storage.load_skill_documents = AsyncMock(
                return_value={
                    "SKILL.md": "# Test Skill\n\nThis is a test skill.",
                }
            )

            await runtime.prepare()
            await runtime.start()

            # Mock chain.astream
            async def mock_astream(*args, **kwargs):
                yield MagicMock(content="Hello")
                yield MagicMock(content=" World")

            with patch.object(runtime, "_chain") as mock_chain:
                mock_chain.astream = mock_astream

                invoke_request = {"user_request": "Test request"}
                chunks = []

                async for chunk in runtime.invoke_stream(invoke_request, timeout=30):
                    chunks.append(chunk)

                assert len(chunks) > 0
                assert chunks[0]["type"] == "chunk"
                assert "Hello" in chunks[0]["content"]

            await runtime.stop()

    @pytest.mark.asyncio
    async def test_invoke_stream_not_running(self, plugin_info, workspace_dir):
        """测试未运行时返回错误"""
        from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
            KnowledgeSkillRuntime,
        )

        runtime = KnowledgeSkillRuntime(plugin_info, workspace_dir)

        invoke_request = {"user_request": "Test request"}
        chunks = []

        async for chunk in runtime.invoke_stream(invoke_request, timeout=30):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0]["type"] == "error"
        assert "未运行" in chunks[0]["error"]

    @pytest.mark.asyncio
    async def test_get_metrics(self, plugin_info, workspace_dir):
        """测试获取运行时指标"""
        from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
            KnowledgeSkillRuntime,
        )

        runtime = KnowledgeSkillRuntime(plugin_info, workspace_dir)

        metrics = await runtime.get_metrics()

        assert "invoke_count" in metrics
        assert "success_count" in metrics
        assert "failure_count" in metrics
        assert "total_duration_ms" in metrics
        assert "recent_errors" in metrics
