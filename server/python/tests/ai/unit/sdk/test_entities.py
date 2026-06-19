# SDK entities 单元测试

import pytest

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.sdk.entities.tool import ToolInvokeMessage


class TestI18nObject:
    """I18nObject 国际化对象测试"""

    def test_init_with_all_languages(self):
        """测试提供所有语言版本"""
        i18n = I18nObject(
            en_US="English text",
            zh_Hans="中文文本",
            pt_BR="Texto em português",
        )

        assert i18n.en_US == "English text"
        assert i18n.zh_Hans == "中文文本"
        assert i18n.pt_BR == "Texto em português"

    def test_init_with_en_only(self):
        """测试仅提供英语版本时，其他语言自动回退"""
        i18n = I18nObject(en_US="English text")

        assert i18n.en_US == "English text"
        assert i18n.zh_Hans == "English text"
        assert i18n.pt_BR == "English text"

    def test_init_with_en_and_zh(self):
        """测试提供英语和中文版本"""
        i18n = I18nObject(
            en_US="English text",
            zh_Hans="中文文本",
        )

        assert i18n.en_US == "English text"
        assert i18n.zh_Hans == "中文文本"
        assert i18n.pt_BR == "English text"

    def test_to_dict(self):
        """测试转换为字典格式"""
        i18n = I18nObject(
            en_US="English text",
            zh_Hans="中文文本",
        )

        result = i18n.to_dict()

        assert isinstance(result, dict)
        assert result["en_US"] == "English text"
        assert result["zh_Hans"] == "中文文本"
        assert result["pt_BR"] == "English text"

    def test_path_property(self):
        """测试 path 属性返回英语版本"""
        i18n = I18nObject(
            en_US="English text",
            zh_Hans="中文文本",
        )

        assert i18n.path == "English text"

    def test_empty_zh_hans_fallback(self):
        """测试空字符串中文版本回退到英语"""
        i18n = I18nObject(en_US="English text", zh_Hans="")

        assert i18n.zh_Hans == "English text"

    def test_none_pt_br_fallback(self):
        """测试 None 葡萄牙语版本回退到英语"""
        i18n = I18nObject(en_US="English text", pt_BR=None)

        assert i18n.pt_BR == "English text"


class TestToolInvokeMessage:
    """ToolInvokeMessage 工具调用消息测试"""

    def test_text_message_creation(self):
        """测试文本消息创建"""
        msg = ToolInvokeMessage.TextMessage(text="Hello, world!")

        assert msg.text == "Hello, world!"
        assert msg.to_dict() == {"text": "Hello, world!"}

    def test_json_message_with_dict(self):
        """测试 JSON 消息（字典）"""
        msg = ToolInvokeMessage.JsonMessage(json_object={"key": "value", "count": 42})

        assert msg.json_object == {"key": "value", "count": 42}
        assert msg.to_dict() == {"json_object": {"key": "value", "count": 42}}

    def test_json_message_with_list(self):
        """测试 JSON 消息（列表）"""
        msg = ToolInvokeMessage.JsonMessage(json_object=[1, 2, 3])

        assert msg.json_object == [1, 2, 3]
        assert msg.to_dict() == {"json_object": [1, 2, 3]}

    def test_blob_message_creation(self):
        """测试二进制消息创建"""
        data = b"\x00\x01\x02\x03"
        msg = ToolInvokeMessage.BlobMessage(blob=data)

        assert msg.blob == data

    def test_blob_chunk_message(self):
        """测试二进制数据块消息"""
        chunk = ToolInvokeMessage.BlobChunkMessage(
            id="chunk-001",
            sequence=1,
            total_length=1024,
            blob=b"\x00\x01",
            end=False,
        )

        assert chunk.id == "chunk-001"
        assert chunk.sequence == 1
        assert chunk.total_length == 1024
        assert chunk.blob == b"\x00\x01"
        assert chunk.end is False

    def test_variable_message_non_stream(self):
        """测试变量消息（非流式）"""
        var = ToolInvokeMessage.VariableMessage(
            variable_name="result",
            variable_value={"status": "success"},
            stream=False,
        )

        assert var.variable_name == "result"
        assert var.variable_value == {"status": "success"}
        assert var.stream is False

    def test_variable_message_stream_with_string(self):
        """测试变量消息（流式，字符串值）"""
        var = ToolInvokeMessage.VariableMessage(
            variable_name="output",
            variable_value="Streaming text...",
            stream=True,
        )

        assert var.variable_name == "output"
        assert var.variable_value == "Streaming text..."
        assert var.stream is True

    def test_variable_message_stream_with_non_string_raises(self):
        """测试流式变量消息使用非字符串值时抛出异常"""
        with pytest.raises(ValueError, match="必须是字符串"):
            ToolInvokeMessage.VariableMessage(
                variable_name="output",
                variable_value={"key": "value"},
                stream=True,
            )
