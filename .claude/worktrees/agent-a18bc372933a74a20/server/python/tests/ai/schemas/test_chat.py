"""AI Chat Schema 单元测试

测试 AIChatRequest、UIMessage 和消息部分的验证逻辑。
"""

import pytest
from pydantic import ValidationError

from ai.schemas.chat import (
    AIChatRequest,
    BodyConfig,
    ImagePart,
    TextPart,
    ToolCallPart,
    ToolResultPart,
    UIMessage,
)
from ai.schemas.completion import ModelConfig, SearchConfig


class TestTextPart:
    """TextPart 测试"""

    def test_valid_text_part(self) -> None:
        """测试有效的文本消息部分"""
        part = TextPart(text="你好")
        assert part.type == "text"
        assert part.text == "你好"

    def test_text_part_type_is_fixed(self) -> None:
        """测试 type 字段固定为 text"""
        part = TextPart(text="测试")
        assert part.type == "text"


class TestImagePart:
    """ImagePart 测试"""

    def test_valid_image_part_with_url(self) -> None:
        """测试有效的图片消息部分（URL）"""
        part = ImagePart(image="https://example.com/image.png")
        assert part.type == "image"
        assert part.image == "https://example.com/image.png"
        assert part.mime_type is None

    def test_image_part_with_mime_type(self) -> None:
        """测试带 MIME 类型的图片消息部分"""
        part = ImagePart(image="base64data", mime_type="image/png")
        assert part.mime_type == "image/png"


class TestToolCallPart:
    """ToolCallPart 测试"""

    def test_valid_tool_call_part(self) -> None:
        """测试有效的工具调用消息部分"""
        part = ToolCallPart(
            tool_call_id="call-123",
            tool_name="search",
            args={"query": "test"},
        )
        assert part.type == "tool-call"
        assert part.tool_call_id == "call-123"
        assert part.tool_name == "search"
        assert part.args == {"query": "test"}

    def test_tool_call_part_default_args(self) -> None:
        """测试工具调用参数默认为空字典"""
        part = ToolCallPart(tool_call_id="call-123", tool_name="search")
        assert part.args == {}


class TestToolResultPart:
    """ToolResultPart 测试"""

    def test_valid_tool_result_part(self) -> None:
        """测试有效的工具结果消息部分"""
        part = ToolResultPart(
            tool_call_id="call-123",
            tool_name="search",
            result={"status": "success"},
        )
        assert part.type == "tool-result"
        assert part.tool_call_id == "call-123"
        assert part.result == {"status": "success"}


class TestUIMessage:
    """UIMessage 测试"""

    def test_valid_user_message(self) -> None:
        """测试有效的用户消息"""
        message = UIMessage(
            id="msg-1",
            role="user",
            parts=[TextPart(text="你好")],
        )
        assert message.id == "msg-1"
        assert message.role == "user"
        assert len(message.parts) == 1

    def test_valid_assistant_message(self) -> None:
        """测试有效的助手消息"""
        message = UIMessage(
            id="msg-2",
            role="assistant",
            parts=[TextPart(text="你好，有什么可以帮助你的？")],
        )
        assert message.role == "assistant"

    def test_valid_system_message(self) -> None:
        """测试有效的系统消息"""
        message = UIMessage(
            id="msg-0",
            role="system",
            parts=[TextPart(text="你是一个友好的助手")],
        )
        assert message.role == "system"

    def test_message_with_multiple_parts(self) -> None:
        """测试包含多个部分的消息"""
        message = UIMessage(
            id="msg-3",
            role="user",
            parts=[
                TextPart(text="请分析这张图片"),
                ImagePart(image="https://example.com/image.png"),
            ],
        )
        assert len(message.parts) == 2

    def test_message_default_parts_is_empty(self) -> None:
        """测试消息部分默认为空列表"""
        message = UIMessage(id="msg-4", role="user")
        assert message.parts == []

    def test_invalid_role_raises_error(self) -> None:
        """测试无效角色引发验证错误"""
        with pytest.raises(ValidationError) as exc_info:
            UIMessage(
                id="msg-5",
                role="invalid_role",  # type: ignore
                parts=[],
            )
        assert "role" in str(exc_info.value)


class TestBodyConfig:
    """BodyConfig 测试"""

    def test_valid_body_config(self) -> None:
        """测试有效的请求体配置"""
        config = BodyConfig(
            model=ModelConfig(provider="openai", name="gpt-4"),
        )
        assert config.model.provider == "openai"
        assert config.model.name == "gpt-4"
        assert config.search is None
        assert config.files is None

    def test_body_config_with_search(self) -> None:
        """测试带搜索配置的请求体"""
        config = BodyConfig(
            model=ModelConfig(provider="openai", name="gpt-4"),
            search=SearchConfig(enabled=True),
        )
        assert config.search is not None
        assert config.search.enabled is True


class TestAIChatRequest:
    """AIChatRequest 测试"""

    def test_valid_chat_request(self) -> None:
        """测试有效的对话请求"""
        request = AIChatRequest(
            id="conv-123",
            messages=[
                UIMessage(
                    id="msg-1",
                    role="user",
                    parts=[TextPart(text="你好")],
                )
            ],
            trigger="submit-message",
            message_id="msg-2",
            body=BodyConfig(
                model=ModelConfig(provider="openai", name="gpt-4"),
            ),
        )
        assert request.id == "conv-123"
        assert len(request.messages) == 1
        assert request.trigger == "submit-message"
        assert request.message_id == "msg-2"

    def test_chat_request_without_id(self) -> None:
        """测试无会话 ID 的对话请求（创建新会话）"""
        request = AIChatRequest(
            messages=[
                UIMessage(
                    id="msg-1",
                    role="user",
                    parts=[TextPart(text="你好")],
                )
            ],
            trigger="submit-message",
            message_id="msg-2",
            body=BodyConfig(
                model=ModelConfig(provider="openai", name="gpt-4"),
            ),
        )
        assert request.id is None

    def test_chat_request_camel_case_alias(self) -> None:
        """测试 camelCase 别名解析（messageId）"""
        # 使用 model_validate 解析原始 JSON 数据
        data = {
            "id": "conv-123",
            "messages": [
                {"id": "msg-1", "role": "user", "parts": [{"type": "text", "text": "你好"}]}
            ],
            "trigger": "submit-message",
            "messageId": "msg-2",  # camelCase
            "body": {
                "model": {"provider": "openai", "name": "gpt-4"},
            },
        }
        request = AIChatRequest.model_validate(data)
        assert request.message_id == "msg-2"

    def test_chat_request_with_regenerate_trigger(self) -> None:
        """测试重新生成触发类型"""
        request = AIChatRequest(
            id="conv-123",
            messages=[
                UIMessage(
                    id="msg-1",
                    role="user",
                    parts=[TextPart(text="你好")],
                )
            ],
            trigger="regenerate",
            message_id="msg-2",
            body=BodyConfig(
                model=ModelConfig(provider="openai", name="gpt-4"),
            ),
        )
        assert request.trigger == "regenerate"

    def test_chat_request_with_edit_message_trigger(self) -> None:
        """测试编辑消息触发类型"""
        request = AIChatRequest(
            id="conv-123",
            messages=[
                UIMessage(
                    id="msg-1",
                    role="user",
                    parts=[TextPart(text="编辑后的消息")],
                )
            ],
            trigger="edit-message",
            message_id="msg-2",
            body=BodyConfig(
                model=ModelConfig(provider="openai", name="gpt-4"),
            ),
        )
        assert request.trigger == "edit-message"

    def test_invalid_trigger_raises_error(self) -> None:
        """测试无效触发类型引发验证错误"""
        with pytest.raises(ValidationError) as exc_info:
            AIChatRequest(
                id="conv-123",
                messages=[
                    UIMessage(id="msg-1", role="user", parts=[TextPart(text="你好")])
                ],
                trigger="invalid_trigger",  # type: ignore
                message_id="msg-2",
                body=BodyConfig(
                    model=ModelConfig(provider="openai", name="gpt-4"),
                ),
            )
        assert "trigger" in str(exc_info.value)

    def test_missing_required_fields_raises_error(self) -> None:
        """测试缺少必填字段引发验证错误"""
        with pytest.raises(ValidationError) as exc_info:
            AIChatRequest(
                messages=[
                    UIMessage(id="msg-1", role="user", parts=[TextPart(text="你好")])
                ],
                # 缺少 trigger、message_id、body
            )  # type: ignore
        errors = exc_info.value.errors()
        error_fields = {e["loc"][0] for e in errors}
        assert "trigger" in error_fields
        # messageId 是 message_id 的 alias，Pydantic 会使用 alias 名称
        assert "messageId" in error_fields or "message_id" in error_fields
        assert "body" in error_fields

    def test_chat_request_model_dump(self) -> None:
        """测试模型序列化"""
        request = AIChatRequest(
            id="conv-123",
            messages=[
                UIMessage(
                    id="msg-1",
                    role="user",
                    parts=[TextPart(text="你好")],
                )
            ],
            trigger="submit-message",
            message_id="msg-2",
            body=BodyConfig(
                model=ModelConfig(provider="openai", name="gpt-4"),
            ),
        )
        data = request.model_dump()
        assert data["id"] == "conv-123"
        assert data["trigger"] == "submit-message"
        assert data["message_id"] == "msg-2"

    def test_chat_request_model_dump_by_alias(self) -> None:
        """测试模型序列化（使用别名）"""
        request = AIChatRequest(
            id="conv-123",
            messages=[
                UIMessage(
                    id="msg-1",
                    role="user",
                    parts=[TextPart(text="你好")],
                )
            ],
            trigger="submit-message",
            message_id="msg-2",
            body=BodyConfig(
                model=ModelConfig(provider="openai", name="gpt-4"),
            ),
        )
        data = request.model_dump(by_alias=True)
        assert data["messageId"] == "msg-2"
