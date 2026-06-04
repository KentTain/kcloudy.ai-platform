"""会话管理控制器单元测试

测试会话列表接口和删除接口的逻辑。
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from ai.controllers.v1.conversation import (
    delete_conversation,
    list_conversations,
)
from ai.schemas.conversation import (
    ConversationDeleteResponse,
    ConversationListResponse,
)


class TestListConversations:
    """会话列表接口测试"""

    @pytest.mark.asyncio
    async def test_list_conversations_no_tenant(self):
        """测试无租户时返回 401"""
        with patch(
            "ai.controllers.v1.conversation.get_tenant_id", return_value=None
        ):
            with pytest.raises(HTTPException) as exc_info:
                await list_conversations()

            assert exc_info.value.status_code == 401
            assert "未授权访问" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_conversations_returns_list(self):
        """测试正常返回会话列表"""
        tenant_id = str(uuid.uuid4())

        # 模拟数据库查询结果
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        mock_row.name = "测试会话"
        mock_row.created_at = datetime.now()
        mock_row.message_count = 5

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        with (
            patch(
                "ai.controllers.v1.conversation.get_tenant_id",
                return_value=tenant_id,
            ),
            patch(
                "ai.controllers.v1.conversation.get_session",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session)),
            ),
        ):
            result = await list_conversations()

            assert isinstance(result, ConversationListResponse)
            assert len(result.conversations) == 1
            assert result.conversations[0].name == "测试会话"
            assert result.conversations[0].message_count == 5

    @pytest.mark.asyncio
    async def test_list_conversations_empty_list(self):
        """测试空会话列表"""
        tenant_id = str(uuid.uuid4())

        mock_result = MagicMock()
        mock_result.all.return_value = []

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        with (
            patch(
                "ai.controllers.v1.conversation.get_tenant_id",
                return_value=tenant_id,
            ),
            patch(
                "ai.controllers.v1.conversation.get_session",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session)),
            ),
        ):
            result = await list_conversations()

            assert isinstance(result, ConversationListResponse)
            assert len(result.conversations) == 0

    @pytest.mark.asyncio
    async def test_list_conversations_exception(self):
        """测试数据库异常处理"""
        tenant_id = str(uuid.uuid4())

        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("数据库连接失败")

        with (
            patch(
                "ai.controllers.v1.conversation.get_tenant_id",
                return_value=tenant_id,
            ),
            patch(
                "ai.controllers.v1.conversation.get_session",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session)),
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await list_conversations()

            assert exc_info.value.status_code == 500


class TestDeleteConversation:
    """删除会话接口测试"""

    @pytest.mark.asyncio
    async def test_delete_conversation_no_tenant(self):
        """测试无租户时返回 401"""
        with patch(
            "ai.controllers.v1.conversation.get_tenant_id", return_value=None
        ):
            with pytest.raises(HTTPException) as exc_info:
                await delete_conversation("conv-123")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self):
        """测试删除不存在的会话返回 404"""
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        with (
            patch(
                "ai.controllers.v1.conversation.get_tenant_id",
                return_value=tenant_id,
            ),
            patch(
                "ai.controllers.v1.conversation.get_session",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock())),
            ),
            patch(
                "ai.controllers.v1.conversation.Conversation.one_by_conditions",
                return_value=None,
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await delete_conversation(conversation_id)

            assert exc_info.value.status_code == 404
            assert "会话不存在" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_conversation_cross_tenant(self):
        """测试跨租户删除返回 404"""
        tenant_id = str(uuid.uuid4())
        other_tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        # 会话属于其他租户
        mock_conversation = MagicMock()
        mock_conversation.tenant_id = other_tenant_id

        with (
            patch(
                "ai.controllers.v1.conversation.get_tenant_id",
                return_value=tenant_id,
            ),
            patch(
                "ai.controllers.v1.conversation.get_session",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock())),
            ),
            patch(
                "ai.controllers.v1.conversation.Conversation.one_by_conditions",
                return_value=None,  # 查询条件包含 tenant_id，跨租户查不到
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await delete_conversation(conversation_id)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_conversation_success(self):
        """测试成功删除会话"""
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        mock_conversation = MagicMock()
        mock_conversation.id = conversation_id
        mock_conversation.tenant_id = tenant_id

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        with (
            patch(
                "ai.controllers.v1.conversation.get_tenant_id",
                return_value=tenant_id,
            ),
            patch(
                "ai.controllers.v1.conversation.get_session",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session)),
            ),
            patch(
                "ai.controllers.v1.conversation.Conversation.one_by_conditions",
                return_value=mock_conversation,
            ),
        ):
            result = await delete_conversation(conversation_id)

            assert isinstance(result, ConversationDeleteResponse)
            assert result.success is True
            # 验证状态被更新为 DELETED
            from ai.models.enums import ConversationStatus

            assert mock_conversation.status == ConversationStatus.DELETED
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_conversation_exception(self):
        """测试删除会话异常处理"""
        tenant_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        with (
            patch(
                "ai.controllers.v1.conversation.get_tenant_id",
                return_value=tenant_id,
            ),
            patch(
                "ai.controllers.v1.conversation.get_session",
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=AsyncMock())
                ),
            ),
            patch(
                "ai.controllers.v1.conversation.Conversation.one_by_conditions",
                side_effect=Exception("数据库错误"),
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await delete_conversation(conversation_id)

            assert exc_info.value.status_code == 500


class TestRouterConfiguration:
    """路由配置测试"""

    def test_router_prefix(self):
        """测试路由前缀"""
        from ai.controllers.v1.conversation import router

        assert router.prefix == "/conversations"

    def test_router_tags(self):
        """测试路由标签"""
        from ai.controllers.v1.conversation import router

        assert "会话管理" in router.tags
