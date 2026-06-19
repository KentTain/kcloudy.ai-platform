"""MessageAdapter unit tests"""

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from ai_plugin.sdk.entities.model.message import (
    AssistantPromptMessage,
    ImagePromptMessageContent,
    SystemPromptMessage,
    TextPromptMessageContent,
    UserPromptMessage,
)
from extended.langchain.models.message_adapter import (
    MessageAdapter,
    UnsupportedMessageTypeError,
    _lc_content_to_platform,
    _platform_content_to_lc,
)


class TestLcContentToPlatform:
    """Tests for _lc_content_to_platform conversion function."""

    def test_str_passthrough(self):
        result = _lc_content_to_platform("hello")
        assert result == "hello"

    def test_none_passthrough(self):
        result = _lc_content_to_platform(None)
        assert result is None

    def test_list_of_str(self):
        result = _lc_content_to_platform(["hello", "world"])
        assert len(result) == 2
        assert all(isinstance(item, TextPromptMessageContent) for item in result)
        assert result[0].data == "hello"
        assert result[1].data == "world"

    def test_list_of_dict_text(self):
        result = _lc_content_to_platform([{"type": "text", "text": "hello"}])
        assert len(result) == 1
        assert isinstance(result[0], TextPromptMessageContent)
        assert result[0].data == "hello"

    def test_list_of_dict_image_url(self):
        result = _lc_content_to_platform(
            [{"type": "image_url", "image_url": {"url": "http://example.com/img.png"}}]
        )
        assert len(result) == 1
        assert isinstance(result[0], ImagePromptMessageContent)
        assert result[0].url == "http://example.com/img.png"

    def test_list_of_dict_unknown_type_fallback(self):
        result = _lc_content_to_platform([{"type": "audio", "data": "test"}])
        assert len(result) == 1
        assert isinstance(result[0], TextPromptMessageContent)
        # Fallback: dict serialized as string
        assert "audio" in result[0].data

    def test_mixed_list(self):
        result = _lc_content_to_platform(
            [
                "hello",
                {"type": "text", "text": "world"},
                {"type": "image_url", "image_url": {"url": "http://img.png"}},
            ]
        )
        assert len(result) == 3
        assert isinstance(result[0], TextPromptMessageContent)
        assert isinstance(result[1], TextPromptMessageContent)
        assert isinstance(result[2], ImagePromptMessageContent)


class TestPlatformContentToLc:
    """Tests for _platform_content_to_lc conversion function."""

    def test_str_passthrough(self):
        result = _platform_content_to_lc("hello")
        assert result == "hello"

    def test_none_passthrough(self):
        result = _platform_content_to_lc(None)
        assert result is None

    def test_list_of_text_content(self):
        tc = TextPromptMessageContent(data="hello")
        result = _platform_content_to_lc([tc])
        assert result == ["hello"]

    def test_list_of_image_content(self):
        ic = ImagePromptMessageContent(
            format="url", url="http://example.com/img.png", mime_type="image/png"
        )
        result = _platform_content_to_lc([ic])
        assert len(result) == 1
        assert result[0]["type"] == "image_url"
        assert result[0]["image_url"]["url"] == "http://example.com/img.png"

    def test_mixed_content_list(self):
        tc = TextPromptMessageContent(data="hello")
        ic = ImagePromptMessageContent(
            format="url", url="http://img.png", mime_type="image/png"
        )
        result = _platform_content_to_lc([tc, ic])
        assert len(result) == 2
        assert result[0] == "hello"
        assert result[1]["type"] == "image_url"

    def test_list_with_str_and_dict_passthrough(self):
        result = _platform_content_to_lc(["hello", {"type": "text", "text": "world"}])
        assert result == ["hello", {"type": "text", "text": "world"}]


class TestToPlatformMessage:
    def test_human_message_to_user(self):
        msg = HumanMessage(content="hello")
        result = MessageAdapter.to_platform_message(msg)
        assert isinstance(result, UserPromptMessage)
        assert result.content == "hello"

    def test_ai_message_to_assistant(self):
        msg = AIMessage(content="hi there")
        result = MessageAdapter.to_platform_message(msg)
        assert isinstance(result, AssistantPromptMessage)
        assert result.content == "hi there"

    def test_system_message_to_system(self):
        msg = SystemMessage(content="you are a helper")
        result = MessageAdapter.to_platform_message(msg)
        assert isinstance(result, SystemPromptMessage)
        assert result.content == "you are a helper"

    def test_human_message_multimodal(self):
        msg = HumanMessage(
            content=[
                {"type": "text", "text": "describe this"},
                {"type": "image_url", "image_url": {"url": "http://img.png"}},
            ]
        )
        result = MessageAdapter.to_platform_message(msg)
        assert isinstance(result, UserPromptMessage)
        assert isinstance(result.content, list)
        assert len(result.content) == 2

    def test_unsupported_type_raises(self):
        msg = ToolMessage(content="result", tool_call_id="t1")
        with pytest.raises(UnsupportedMessageTypeError) as exc_info:
            MessageAdapter.to_platform_message(msg)
        assert "ToolMessage" in str(exc_info.value)


class TestToPlatformMessages:
    def test_batch_conversion(self):
        msgs = [
            SystemMessage(content="system"),
            HumanMessage(content="user"),
            AIMessage(content="assistant"),
        ]
        result = MessageAdapter.to_platform_messages(msgs)
        assert len(result) == 3
        assert isinstance(result[0], SystemPromptMessage)
        assert isinstance(result[1], UserPromptMessage)
        assert isinstance(result[2], AssistantPromptMessage)

    def test_empty_list(self):
        result = MessageAdapter.to_platform_messages([])
        assert result == []

    def test_batch_with_unsupported_raises(self):
        msgs = [HumanMessage(content="ok"), ToolMessage(content="x", tool_call_id="t1")]
        with pytest.raises(UnsupportedMessageTypeError):
            MessageAdapter.to_platform_messages(msgs)


class TestToLangchainMessage:
    def test_user_to_human_message(self):
        msg = UserPromptMessage(content="hello")
        result = MessageAdapter.to_langchain_message(msg)
        assert isinstance(result, HumanMessage)
        assert result.content == "hello"

    def test_assistant_to_ai_message(self):
        msg = AssistantPromptMessage(content="hi there")
        result = MessageAdapter.to_langchain_message(msg)
        assert isinstance(result, AIMessage)
        assert result.content == "hi there"

    def test_system_to_system_message(self):
        msg = SystemPromptMessage(content="you are a helper")
        result = MessageAdapter.to_langchain_message(msg)
        assert isinstance(result, SystemMessage)
        assert result.content == "you are a helper"

    def test_user_with_image_content(self):
        msg = UserPromptMessage(
            content=[
                TextPromptMessageContent(data="describe this"),
                ImagePromptMessageContent(
                    format="url", url="http://img.png", mime_type="image/png"
                ),
            ]
        )
        result = MessageAdapter.to_langchain_message(msg)
        assert isinstance(result, HumanMessage)
        assert isinstance(result.content, list)
        assert len(result.content) == 2
        assert result.content[0] == "describe this"
        assert result.content[1]["type"] == "image_url"

    def test_unsupported_type_raises(self):
        from ai_plugin.sdk.entities.model.message import ToolPromptMessage

        msg = ToolPromptMessage(content="result", tool_call_id="t1")
        with pytest.raises(UnsupportedMessageTypeError) as exc_info:
            MessageAdapter.to_langchain_message(msg)
        assert "ToolPromptMessage" in str(exc_info.value)


class TestRoundTrip:
    def test_human_round_trip(self):
        original = HumanMessage(content="test")
        platform = MessageAdapter.to_platform_message(original)
        back = MessageAdapter.to_langchain_message(platform)
        assert isinstance(back, HumanMessage)
        assert back.content == original.content

    def test_ai_round_trip(self):
        original = AIMessage(content="response")
        platform = MessageAdapter.to_platform_message(original)
        back = MessageAdapter.to_langchain_message(platform)
        assert isinstance(back, AIMessage)
        assert back.content == original.content

    def test_system_round_trip(self):
        original = SystemMessage(content="instruction")
        platform = MessageAdapter.to_platform_message(original)
        back = MessageAdapter.to_langchain_message(platform)
        assert isinstance(back, SystemMessage)
        assert back.content == original.content

    def test_multimodal_round_trip(self):
        original = HumanMessage(
            content=[
                {"type": "text", "text": "describe"},
                {"type": "image_url", "image_url": {"url": "http://img.png"}},
            ]
        )
        platform = MessageAdapter.to_platform_message(original)
        back = MessageAdapter.to_langchain_message(platform)
        assert isinstance(back, HumanMessage)
        assert isinstance(back.content, list)
        assert back.content[0] == "describe"
        assert back.content[1]["type"] == "image_url"
        assert back.content[1]["image_url"]["url"] == "http://img.png"
