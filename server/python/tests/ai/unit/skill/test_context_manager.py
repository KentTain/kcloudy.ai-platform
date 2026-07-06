"""Skill Context Manager 单元测试"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.components.skill.context_manager import (
    SkillContextManager,
    SkillExecutionContext,
)


class TestSkillContextManager:
    """测试 SkillContextManager"""

    def test_context_key_format(self):
        """验证上下文键格式"""
        manager = SkillContextManager()

        # Act
        key = manager._build_context_key("tenant1", "user1", "skill1")

        # Assert
        assert key == "tenant1:user1:skill1"

    def test_cache_context(self):
        """验证上下文缓存"""
        manager = SkillContextManager()

        # Act - 加载 Skill
        manager.load_skill(
            skill_id="skill1",
            user_id="user1",
            tenant_id="tenant1",
            conversation_id="conv1",
            skill_document="测试文档",
        )

        # Assert - 验证上下文已缓存
        key = manager._build_context_key("tenant1", "user1", "skill1")
        assert key in manager._contexts
        context = manager._contexts[key]
        assert context.skill_id == "skill1"
        assert context.user_id == "user1"
        assert context.tenant_id == "tenant1"

    @pytest.mark.asyncio
    async def test_invoke_skill_updates_stats(self):
        """验证调用更新统计信息"""
        manager = SkillContextManager()

        # Arrange - 设置 mock LLM
        mock_llm = MagicMock()
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value="响应内容")
        manager.set_llm(mock_llm)

        # Act - 加载并调用 Skill
        manager.load_skill(
            skill_id="skill1",
            user_id="user1",
            tenant_id="tenant1",
            conversation_id="conv1",
            skill_document="测试文档",
        )

        # 获取上下文并手动设置 chain_cache
        key = manager._build_context_key("tenant1", "user1", "skill1")
        context = manager._contexts[key]
        context.chain_cache["default"] = mock_chain

        # 调用 skill
        result = await manager.invoke_skill(
            skill_id="skill1",
            user_request="你好",
            tenant_id="tenant1",
            user_id="user1",
        )

        # Assert - 验证统计信息已更新
        assert context.invoke_count == 1
        assert context.last_invoked_at is not None
        assert isinstance(context.last_invoked_at, datetime)

    @pytest.mark.asyncio
    async def test_invoke_skill_not_loaded(self):
        """验证未加载时抛出 RuntimeError"""
        manager = SkillContextManager()

        # Act & Assert - 调用未加载的 Skill
        with pytest.raises(RuntimeError, match="Skill not loaded"):
            await manager.invoke_skill(
                skill_id="skill1",
                user_request="你好",
                tenant_id="tenant1",
                user_id="user1",
            )

    def test_format_examples(self):
        """验证格式化示例文档"""
        manager = SkillContextManager()

        # Arrange
        examples = {
            "example1": "示例1内容",
            "example2": "示例2内容",
        }

        # Act
        formatted = manager._format_examples(examples)

        # Assert
        assert "example1: 示例1内容" in formatted
        assert "example2: 示例2内容" in formatted

    def test_format_empty_examples(self):
        """验证格式化空示例"""
        manager = SkillContextManager()

        # Act
        formatted = manager._format_examples(None)
        formatted_empty_dict = manager._format_examples({})

        # Assert
        assert formatted == ""
        assert formatted_empty_dict == ""

    def test_context_dataclass_fields(self):
        """验证上下文数据类字段"""
        # Act
        context = SkillExecutionContext(
            skill_id="skill1",
            skill_name="测试技能",
            skill_type="knowledge",
            user_id="user1",
            tenant_id="tenant1",
            conversation_id="conv1",
        )

        # Assert - 验证必需字段
        assert context.skill_id == "skill1"
        assert context.skill_name == "测试技能"
        assert context.skill_type == "knowledge"
        assert context.user_id == "user1"
        assert context.tenant_id == "tenant1"
        assert context.conversation_id == "conv1"

        # Assert - 验证默认值字段
        assert context.message_history == []
        assert context.skill_document == ""
        assert context.examples == {}
        assert isinstance(context.loaded_at, datetime)
        assert context.invoke_count == 0
        assert context.last_invoked_at is None
        assert context.chain_cache == {}
