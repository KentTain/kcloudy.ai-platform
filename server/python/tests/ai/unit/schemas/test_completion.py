"""LLM 对话 Schema 测试"""

import pytest
from ai.schemas.completion import (
    ModelConfig,
    SearchConfig,
    FileItem,
    LLMChatCompletion,
    SSEMessageEvent,
    SSEFinishEvent,
    SSESearchEvent,
    SSEErrorEvent,
    ErrorCode,
)


class TestModelConfig:
    """ModelConfig 测试"""

    def test_create_model_config(self):
        """测试创建模型配置"""
        config = ModelConfig(provider="openai", name="gpt-4")
        assert config.provider == "openai"
        assert config.name == "gpt-4"
        assert config.completion_params == {"temperature": 0.7}

    def test_model_config_with_params(self):
        """测试带参数的模型配置"""
        config = ModelConfig(
            provider="openai",
            name="gpt-4",
            completion_params={"temperature": 0.5, "max_tokens": 1000},
        )
        assert config.completion_params["temperature"] == 0.5
        assert config.completion_params["max_tokens"] == 1000


class TestSearchConfig:
    """SearchConfig 测试"""

    def test_default_search_config(self):
        """测试默认搜索配置"""
        config = SearchConfig()
        assert config.enabled is False
        assert config.provider == "baidu"

    def test_enabled_search_config(self):
        """测试启用搜索配置"""
        config = SearchConfig(enabled=True)
        assert config.enabled is True


class TestFileItem:
    """FileItem 测试"""

    def test_file_item_remote_url(self):
        """测试远程 URL 文件项"""
        item = FileItem(type="image", transfer_method="remote_url", url="https://example.com/image.png")
        assert item.type == "image"
        assert item.transfer_method == "remote_url"
        assert item.url == "https://example.com/image.png"

    def test_file_item_invalid_type(self):
        """测试无效文件类型"""
        with pytest.raises(ValueError, match="当前仅支持图片格式"):
            FileItem(type="video", transfer_method="remote_url")

    def test_file_item_invalid_transfer_method(self):
        """测试无效传递方式"""
        with pytest.raises(ValueError, match="传递方式必须是"):
            FileItem(type="image", transfer_method="invalid")


class TestLLMChatCompletion:
    """LLMChatCompletion 测试"""

    def test_create_chat_completion(self):
        """测试创建对话请求"""
        request = LLMChatCompletion(
            model=ModelConfig(provider="openai", name="gpt-4"),
            query="你好",
        )
        assert request.query == "你好"
        assert request.conversation_id is None
        assert request.files is None
        assert request.search is None

    def test_chat_completion_with_conversation(self):
        """测试带会话 ID 的对话请求"""
        request = LLMChatCompletion(
            model=ModelConfig(provider="openai", name="gpt-4"),
            query="继续对话",
            conversation_id="123e4567-e89b-12d3-a456-426614174000",
        )
        assert request.conversation_id == "123e4567-e89b-12d3-a456-426614174000"


class TestSSEEvents:
    """SSE 事件测试"""

    def test_message_event(self):
        """测试 message 事件"""
        event = SSEMessageEvent(data={"content": "你好"})
        assert event.event == "message"
        assert event.data.content == "你好"

    def test_finish_event(self):
        """测试 finish 事件"""
        event = SSEFinishEvent(data={"prompt_tokens": 10, "completion_tokens": 20})
        assert event.event == "finish"
        assert event.data.prompt_tokens == 10
        assert event.data.completion_tokens == 20

    def test_search_event(self):
        """测试 search_keywords 事件"""
        event = SSESearchEvent(data={"keywords": ["关键词1", "关键词2"]})
        assert event.event == "search_keywords"
        assert event.data.keywords == ["关键词1", "关键词2"]

    def test_error_event(self):
        """测试 error 事件"""
        event = SSEErrorEvent(data={"code": ErrorCode.MODEL_ERROR, "message": "模型调用失败"})
        assert event.event == "error"
        assert event.data.code == ErrorCode.MODEL_ERROR
        assert event.data.message == "模型调用失败"


class TestErrorCode:
    """错误代码测试"""

    def test_error_codes_defined(self):
        """测试错误代码已定义"""
        assert ErrorCode.MODEL_ERROR == "MODEL_ERROR"
        assert ErrorCode.PROVIDER_ERROR == "PROVIDER_ERROR"
        assert ErrorCode.TIMEOUT_ERROR == "TIMEOUT_ERROR"
        assert ErrorCode.CONVERSATION_NOT_FOUND == "CONVERSATION_NOT_FOUND"
        assert ErrorCode.PERMISSION_DENIED == "PERMISSION_DENIED"
