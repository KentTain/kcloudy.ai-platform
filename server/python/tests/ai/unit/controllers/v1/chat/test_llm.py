"""LLM 对话控制器测试"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai.controllers.v1.chat.llm import (
    EventType,
    _format_sse_line,
    _is_search_tool,
    router,
)


class TestRouterConfiguration:
    """路由配置测试"""

    def test_router_prefix(self):
        """测试路由前缀"""
        assert router.prefix == "/chat-messages"

    def test_router_tags(self):
        """测试路由标签"""
        assert "LLM对话" in router.tags


class TestSearchToolDetection:
    """搜索工具检测测试"""

    def test_is_search_tool_baidu(self):
        """测试百度搜索工具"""
        assert _is_search_tool("baidu_search") is True

    def test_is_search_tool_google(self):
        """测试 Google 搜索工具"""
        assert _is_search_tool("google_search") is True

    def test_is_search_tool_bing(self):
        """测试 Bing 搜索工具"""
        assert _is_search_tool("bing_websearch") is True

    def test_is_search_tool_non_search(self):
        """测试非搜索工具"""
        assert _is_search_tool("calculator") is False

    def test_is_search_tool_empty(self):
        """测试空工具名"""
        assert _is_search_tool("") is False

    def test_is_search_tool_none(self):
        """测试 None 工具名"""
        assert _is_search_tool(None) is False


class TestSSEFormatting:
    """SSE 格式化测试"""

    def test_format_sse_line_dict(self):
        """测试字典数据格式化"""
        data = {"event": "message", "data": {"content": "你好"}}
        result = _format_sse_line(data)
        assert result.startswith("data: ")
        assert result.endswith("\n\n")
        assert "message" in result

    def test_format_sse_line_string(self):
        """测试字符串数据格式化"""
        data = '{"event": "message"}'
        result = _format_sse_line(data)
        assert result == f"data: {data}\n\n"


class TestEventType:
    """事件类型测试"""

    def test_event_types_defined(self):
        """测试事件类型已定义"""
        assert EventType.START == "start"
        assert EventType.TEXT_START == "text-start"
        assert EventType.TEXT_DELTA == "text-delta"
        assert EventType.TEXT_END == "text-end"
        assert EventType.TOOL_CALL == "tool-call"
        assert EventType.TOOL_RESULT == "tool-result"
        assert EventType.FINISH == "finish"
        assert EventType.ERROR == "error"


def _make_async_gen_mock(value=None):
    """创建异步生成器 mock"""
    async def gen():
        yield value
    return gen()


class TestTenantIsolation:
    """租户隔离测试"""

    @pytest.mark.asyncio
    async def test_stop_chat_cross_tenant_returns_404(self):
        """测试跨租户停止对话返回 404（get_by_id 会过滤 tenant_id）"""
        from fastapi import HTTPException

        from ai.controllers.v1.chat.llm import stop_chat_messages

        # Mock get_tenant_id 返回当前租户
        with patch("ai.controllers.v1.chat.llm.get_tenant_id", return_value="tenant-1"):
            # conversation_service.get_by_id 会对 tenant_id 过滤，跨租户返回 None
            with patch(
                "ai.controllers.v1.chat.llm.conversation_service.get_by_id",
                new_callable=AsyncMock,
                return_value=None,  # 跨租户查不到
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await stop_chat_messages("conv-1")

                assert exc_info.value.status_code == 404
                assert "会话不存在" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_stop_chat_not_found_returns_404(self):
        """测试停止不存在的会话返回 404"""
        from fastapi import HTTPException

        from ai.controllers.v1.chat.llm import stop_chat_messages

        with patch("ai.controllers.v1.chat.llm.get_tenant_id", return_value="tenant-1"):
            with patch(
                "ai.controllers.v1.chat.llm.conversation_service.get_by_id",
                new_callable=AsyncMock,
                return_value=None,
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await stop_chat_messages("nonexistent-conv")

                assert exc_info.value.status_code == 404
                assert "会话不存在" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_stop_chat_same_tenant_success(self):
        """测试同租户停止对话成功"""
        from ai.controllers.v1.chat.llm import stop_chat_messages

        # Mock get_tenant_id 返回当前租户
        with patch("ai.controllers.v1.chat.llm.get_tenant_id", return_value="tenant-1"):
            # Mock 会话属于同一租户
            mock_conversation = Mock()
            mock_conversation.tenant_id = "tenant-1"  # 同一租户

            with patch(
                "ai.controllers.v1.chat.llm.conversation_service.get_by_id",
                new_callable=AsyncMock,
                return_value=mock_conversation,
            ), patch(
                "ai.controllers.v1.chat.llm.ACTIVE_ASYNCIO_TASKS",
                {"generate:llm": {}},
            ):
                result = await stop_chat_messages("conv-1")
                assert result["success"] is True
                assert "未找到活跃任务" in result["message"]
