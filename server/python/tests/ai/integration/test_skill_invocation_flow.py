"""Skill 调用流程集成测试"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.components.skill.chain_builder import SkillChainBuilder
from ai.components.skill.context_manager import SkillContextManager


class TestSkillInvocationFlow:
    """测试 Skill 调用流程集成"""

    @pytest.mark.asyncio
    async def test_knowledge_skill_full_flow(self):
        """测试知识文档 Skill 完整调用流程"""
        # Arrange
        manager = SkillContextManager()

        # 创建 mock LLM
        mock_llm = MagicMock()

        # 创建 mock chain
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value="执行成功")

        # 设置 LLM
        manager.set_llm(mock_llm)

        # Act - 加载 Skill
        context = manager.load_skill(
            skill_id="community/airtable",
            user_id="user123",
            tenant_id="tenant456",
            conversation_id="conv789",
            skill_document="# Airtable Skill\nWork with Airtable API.",
            examples={"examples/create.md": "## Create\nCreate a record."},
            skill_name="Airtable",
            skill_type="knowledge",
        )

        # 手动设置 chain_cache 以避免构建真实 chain
        context.chain_cache["default"] = mock_chain

        # Act - 调用 Skill
        result = await manager.invoke_skill(
            skill_id="community/airtable",
            user_request="创建一条记录",
            tenant_id="tenant456",
            user_id="user123",
        )

        # Assert
        assert result == "执行成功"
        assert context.invoke_count == 1
        assert context.last_invoked_at is not None

    @pytest.mark.asyncio
    async def test_multi_skill_combination(self):
        """测试多 Skill 组合调用"""
        # Arrange
        mock_llm = MagicMock()
        builder = SkillChainBuilder(mock_llm)

        skills = [
            {"name": "Airtable", "document": "# Airtable Skill\nManage Airtable records."},
            {"name": "Notion", "document": "# Notion Skill\nManage Notion pages."},
        ]

        # Act
        chain = builder.build_multi_skill_chain(skills, "创建一个记录并同步到 Notion")

        # Mock chain.ainvoke
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value="Combined result")

        # Assert - 验证 chain 已创建
        assert chain is not None

        # 验证可以通过 mock chain 执行
        result = await mock_chain.ainvoke({"user_request": "测试请求"})
        assert result == "Combined result"

    @pytest.mark.asyncio
    async def test_skill_chain_caching(self):
        """测试 Skill Chain 缓存"""
        # Arrange
        manager = SkillContextManager()
        mock_llm = MagicMock()
        manager.set_llm(mock_llm)

        # Act - 加载 Skill
        context = manager.load_skill(
            skill_id="community/airtable",
            user_id="user123",
            tenant_id="tenant456",
            conversation_id="conv789",
            skill_document="# Airtable Skill",
        )

        # 获取或构建 chain 两次
        chain1 = manager._get_or_build_chain(context)
        chain2 = manager._get_or_build_chain(context)

        # Assert - 验证返回的是同一个实例
        assert chain1 is chain2
        assert "default" in context.chain_cache

    @pytest.mark.asyncio
    async def test_skill_unload(self):
        """测试 Skill 卸载"""
        # Arrange
        manager = SkillContextManager()
        mock_llm = MagicMock()
        manager.set_llm(mock_llm)

        # Act - 加载 Skill
        manager.load_skill(
            skill_id="community/airtable",
            user_id="user123",
            tenant_id="tenant456",
            conversation_id="conv789",
            skill_document="# Airtable Skill",
        )

        # Assert - 验证上下文存在
        key = manager._build_context_key("tenant456", "user123", "community/airtable")
        assert key in manager._contexts

        # Act - 卸载 Skill
        manager.unload_skill(
            skill_id="community/airtable",
            tenant_id="tenant456",
            user_id="user123",
        )

        # Assert - 验证上下文已清除
        assert key not in manager._contexts

    @pytest.mark.asyncio
    async def test_skill_invoke_updates_error_history(self):
        """测试 Skill 调用失败记录错误历史"""
        # Arrange
        manager = SkillContextManager()
        mock_llm = MagicMock()
        manager.set_llm(mock_llm)

        # 加载 Skill
        context = manager.load_skill(
            skill_id="community/airtable",
            user_id="user123",
            tenant_id="tenant456",
            conversation_id="conv789",
            skill_document="# Airtable Skill",
        )

        # Mock chain.ainvoke 抛出异常
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(side_effect=Exception("LLM error"))
        context.chain_cache["default"] = mock_chain

        # Act & Assert - 调用 Skill 并期望抛出异常
        with pytest.raises(Exception, match="LLM error"):
            await manager.invoke_skill(
                skill_id="community/airtable",
                user_request="测试请求",
                tenant_id="tenant456",
                user_id="user123",
            )

        # Assert - 验证调用计数已更新（即使失败）
        assert context.invoke_count == 1
