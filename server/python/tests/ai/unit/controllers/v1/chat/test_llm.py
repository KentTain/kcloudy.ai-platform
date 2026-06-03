"""LLM 对话控制器测试"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from ai.controllers.v1.chat.llm import router, _is_search_tool, _format_sse_line, EventType


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
        assert EventType.READY == "ready"
        assert EventType.MESSAGE == "message"
        assert EventType.FINISH == "finish"
        assert EventType.ERROR == "error"
        assert EventType.SEARCH_KEYWORDS == "search_keywords"
        assert EventType.STOP == "stop"
        assert EventType.CLOSE == "close"
