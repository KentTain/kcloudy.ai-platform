"""AI Chat Controller 单元测试

测试 LLM 对话控制器中的辅助函数和请求处理逻辑。
"""

import pytest

from ai.controllers.v1.chat.llm import (
    _extract_user_query,
    _format_sse_line,
    _is_search_tool,
)
from ai.schemas.chat import AIChatRequest, TextPart, UIMessage


class TestIsSearchTool:
    """_is_search_tool 测试"""

    def test_search_keyword(self) -> None:
        """测试 search 关键字"""
        assert _is_search_tool("search") is True
        assert _is_search_tool("web_search") is True
        assert _is_search_tool("my_search_tool") is True

    def test_baidu_keyword(self) -> None:
        """测试 baidu 关键字"""
        assert _is_search_tool("baidu_search") is True
        assert _is_search_tool("BaiduSearch") is True

    def test_google_keyword(self) -> None:
        """测试 google 关键字"""
        assert _is_search_tool("google_search") is True
        assert _is_search_tool("GoogleCustomSearch") is True

    def test_bing_keyword(self) -> None:
        """测试 bing 关键字"""
        assert _is_search_tool("bing_search") is True

    def test_duckduckgo_keyword(self) -> None:
        """测试 duckduckgo 关键字"""
        assert _is_search_tool("duckduckgo_search") is True

    def test_websearch_keyword(self) -> None:
        """测试 websearch 关键字"""
        assert _is_search_tool("websearch") is True

    def test_non_search_tool(self) -> None:
        """测试非搜索工具"""
        assert _is_search_tool("calculator") is False
        assert _is_search_tool("translator") is False
        assert _is_search_tool("code_runner") is False

    def test_empty_string(self) -> None:
        """测试空字符串"""
        assert _is_search_tool("") is False

    def test_none_value(self) -> None:
        """测试 None 值"""
        assert _is_search_tool(None) is False  # type: ignore


class TestExtractUserQuery:
    """_extract_user_query 测试"""

    def test_extract_from_single_user_message(self) -> None:
        """测试从单条用户消息提取查询"""
        messages = [
            UIMessage(
                id="msg-1",
                role="user",
                parts=[TextPart(text="你好")],
            )
        ]
        query = _extract_user_query(messages)
        assert query == "你好"

    def test_extract_from_last_user_message(self) -> None:
        """测试从最后一条用户消息提取查询"""
        messages = [
            UIMessage(
                id="msg-1",
                role="user",
                parts=[TextPart(text="第一条消息")],
            ),
            UIMessage(
                id="msg-2",
                role="assistant",
                parts=[TextPart(text="回复")],
            ),
            UIMessage(
                id="msg-3",
                role="user",
                parts=[TextPart(text="第二条消息")],
            ),
        ]
        query = _extract_user_query(messages)
        assert query == "第二条消息"

    def test_extract_skips_assistant_messages(self) -> None:
        """测试跳过助手消息"""
        messages = [
            UIMessage(
                id="msg-1",
                role="assistant",
                parts=[TextPart(text="助手消息")],
            ),
            UIMessage(
                id="msg-2",
                role="user",
                parts=[TextPart(text="用户消息")],
            ),
        ]
        query = _extract_user_query(messages)
        assert query == "用户消息"

    def test_extract_from_mixed_parts(self) -> None:
        """测试从混合部分提取文本"""
        from ai.schemas.chat import ImagePart

        messages = [
            UIMessage(
                id="msg-1",
                role="user",
                parts=[
                    ImagePart(image="https://example.com/image.png"),
                    TextPart(text="请分析这张图片"),
                ],
            )
        ]
        query = _extract_user_query(messages)
        assert query == "请分析这张图片"

    def test_extract_from_dict_part(self) -> None:
        """测试从 dict 类型的 part 提取文本"""
        # 模拟 Pydantic 解析为 dict 的情况
        messages = [
            UIMessage(
                id="msg-1",
                role="user",
                parts=[{"type": "text", "text": "dict 消息"}],  # type: ignore
            )
        ]
        query = _extract_user_query(messages)
        assert query == "dict 消息"

    def test_raise_error_when_no_user_message(self) -> None:
        """测试没有用户消息时引发错误"""
        messages = [
            UIMessage(
                id="msg-1",
                role="assistant",
                parts=[TextPart(text="助手消息")],
            )
        ]
        with pytest.raises(ValueError, match="无法从消息中提取用户查询"):
            _extract_user_query(messages)

    def test_raise_error_when_no_text_part(self) -> None:
        """测试用户消息没有文本部分时引发错误"""
        from ai.schemas.chat import ImagePart

        messages = [
            UIMessage(
                id="msg-1",
                role="user",
                parts=[ImagePart(image="https://example.com/image.png")],
            )
        ]
        with pytest.raises(ValueError, match="无法从消息中提取用户查询"):
            _extract_user_query(messages)

    def test_raise_error_when_empty_messages(self) -> None:
        """测试空消息列表时引发错误"""
        messages: list[UIMessage] = []
        with pytest.raises(ValueError, match="无法从消息中提取用户查询"):
            _extract_user_query(messages)


class TestFormatSseLine:
    """_format_sse_line 测试"""

    def test_format_string_data(self) -> None:
        """测试格式化字符串数据"""
        result = _format_sse_line("[DONE]")
        assert result == "data: [DONE]\n\n"

    def test_format_dict_data(self) -> None:
        """测试格式化字典数据"""
        result = _format_sse_line({"type": "text-delta", "delta": "你好"})
        assert result == 'data: {"type":"text-delta","delta":"你好"}\n\n'

    def test_format_nested_dict(self) -> None:
        """测试格式化嵌套字典"""
        data = {
            "type": "finish",
            "usage": {"promptTokens": 10, "completionTokens": 20},
        }
        result = _format_sse_line(data)
        assert "data:" in result
        assert "promptTokens" in result
        assert "completionTokens" in result

    def test_format_with_unicode(self) -> None:
        """测试格式化包含 Unicode 的数据"""
        result = _format_sse_line({"text": "你好世界"})
        assert "你好世界" in result


class TestAIChatRequestIntegration:
    """AIChatRequest 集成测试"""

    def test_full_request_validation(self) -> None:
        """测试完整请求验证"""

        data = {
            "id": "conv-123",
            "messages": [
                {"id": "msg-1", "role": "user", "parts": [{"type": "text", "text": "你好"}]},
                {"id": "msg-2", "role": "assistant", "parts": [{"type": "text", "text": "你好！"}]},
                {"id": "msg-3", "role": "user", "parts": [{"type": "text", "text": "今天天气怎么样？"}]},
            ],
            "trigger": "submit-message",
            "messageId": "msg-4",
            "body": {
                "model": {"provider": "openai", "name": "gpt-4", "completionParams": {"temperature": 0.7}},
            },
        }
        request = AIChatRequest.model_validate(data)

        # 验证请求结构
        assert request.id == "conv-123"
        assert len(request.messages) == 3
        assert request.trigger == "submit-message"
        assert request.message_id == "msg-4"
        assert request.body.model.provider == "openai"

        # 验证提取用户查询
        query = _extract_user_query(request.messages)
        assert query == "今天天气怎么样？"

    def test_request_with_tool_calls(self) -> None:
        """测试包含工具调用的请求"""
        data = {
            "id": "conv-456",
            "messages": [
                {
                    "id": "msg-1",
                    "role": "user",
                    "parts": [{"type": "text", "text": "搜索 Python 教程"}],
                },
                {
                    "id": "msg-2",
                    "role": "assistant",
                    "parts": [
                        {
                            "type": "tool-call",
                            "tool_call_id": "call-1",
                            "tool_name": "web_search",
                            "args": {"query": "Python 教程"},
                        }
                    ],
                },
                {
                    "id": "msg-3",
                    "role": "user",
                    "parts": [
                        {
                            "type": "tool-result",
                            "tool_call_id": "call-1",
                            "tool_name": "web_search",
                            "result": {"links": ["https://example.com"]},
                        }
                    ],
                },
            ],
            "trigger": "submit-message",
            "messageId": "msg-4",
            "body": {"model": {"provider": "openai", "name": "gpt-4"}},
        }
        request = AIChatRequest.model_validate(data)

        # 验证工具调用解析
        assert len(request.messages) == 3
        assert len(request.messages[1].parts) == 1
        # 工具调用部分被解析为 ToolCallPart
        tool_call_part = request.messages[1].parts[0]
        assert tool_call_part.type == "tool-call"  # type: ignore
        assert tool_call_part.tool_name == "web_search"  # type: ignore

        # 工具结果部分
        tool_result_part = request.messages[2].parts[0]
        assert tool_result_part.type == "tool-result"  # type: ignore
