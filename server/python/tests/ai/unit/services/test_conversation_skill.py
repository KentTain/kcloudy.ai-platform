"""对话服务 Skill 调用单元测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ai.services.conversation import ConversationService


class TestConversationServiceSkill:
    """对话服务 Skill 调用测试"""

    @pytest.fixture
    def service(self):
        return ConversationService()

    @pytest.mark.asyncio
    async def test_chat_with_skill_single_skill(self, service):
        """测试单 Skill 调用"""
        mock_context = MagicMock()
        mock_context.skill_id = "community/airtable"
        mock_context.skill_name = "airtable"
        mock_context.skill_document = "# Airtable Skill"
        mock_context.examples = {}

        with patch(
            "ai.services.conversation_service.skill_context_manager.load_skill",
            new_callable=AsyncMock,
            return_value=mock_context,
        ), patch(
            "ai.services.conversation_service.skill_context_manager.invoke_skill",
            new_callable=AsyncMock,
            return_value="Skill response",
        ):
            results = []
            async for result in service.chat_with_skill(
                conversation_id="conv-001",
                user_message="Create a record",
                skill_ids=["community/airtable"],
                user_id="user-001",
                tenant_id="tenant-001",
            ):
                results.append(result)

        assert any(r["type"] == "complete" for r in results)

    @pytest.mark.asyncio
    async def test_chat_with_skill_multiple_skills(self, service):
        """测试多 Skill 组合调用"""
        mock_context = MagicMock()
        mock_context.skill_id = "community/airtable"
        mock_context.skill_document = "# Skill"
        mock_context.examples = {}

        with patch(
            "ai.services.conversation_service.skill_context_manager.load_skill",
            new_callable=AsyncMock,
            return_value=mock_context,
        ), patch(
            "ai.services.conversation_service.skill_context_manager.invoke_skill",
            new_callable=AsyncMock,
            return_value="Combined response",
        ):
            results = []
            async for result in service.chat_with_skill(
                conversation_id="conv-001",
                user_message="Combine skills",
                skill_ids=["community/airtable", "community/notion"],
                user_id="user-001",
                tenant_id="tenant-001",
            ):
                results.append(result)

        assert any(r["type"] == "complete" for r in results)

    @pytest.mark.asyncio
    async def test_chat_with_skill_empty_skill_ids(self, service):
        """测试空 Skill 列表"""
        results = []
        async for result in service.chat_with_skill(
            conversation_id="conv-001",
            user_message="test",
            skill_ids=[],
            user_id="user-001",
            tenant_id="tenant-001",
        ):
            results.append(result)

        assert len(results) == 1
        assert results[0]["type"] == "error"
