# SDK file 单元测试

import pytest

from ai_plugin.sdk.file.constants import (
    DIFY_FILE_IDENTITY,
    DIFY_TOOL_SELECTOR_IDENTITY,
    FILE_MODEL_IDENTITY,
)
from ai_plugin.sdk.file.entities import FileType


class TestFileConstants:
    """文件常量测试"""

    def test_dify_file_identity(self):
        """测试 Dify 文件标识常量"""
        assert DIFY_FILE_IDENTITY == "__dify__file__"
        assert isinstance(DIFY_FILE_IDENTITY, str)

    def test_dify_tool_selector_identity(self):
        """测试 Dify 工具选择器标识常量"""
        assert DIFY_TOOL_SELECTOR_IDENTITY == "__dify__tool_selector__"
        assert isinstance(DIFY_TOOL_SELECTOR_IDENTITY, str)

    def test_file_model_identity(self):
        """测试文件模型标识常量"""
        assert FILE_MODEL_IDENTITY == "__fly__file__"
        assert isinstance(FILE_MODEL_IDENTITY, str)

    def test_constants_are_unique(self):
        """测试所有常量值唯一"""
        constants = [
            DIFY_FILE_IDENTITY,
            DIFY_TOOL_SELECTOR_IDENTITY,
            FILE_MODEL_IDENTITY,
        ]
        
        assert len(constants) == len(set(constants))


class TestFileType:
    """FileType 文件类型枚举测试"""

    def test_file_type_is_str_enum(self):
        """测试 FileType 继承自 StrEnum"""
        from enum import StrEnum
        
        assert issubclass(FileType, StrEnum)

    def test_image_type(self):
        """测试图像文件类型"""
        assert FileType.IMAGE == "image"
        assert FileType.IMAGE.value == "image"

    def test_document_type(self):
        """测试文档文件类型"""
        assert FileType.DOCUMENT == "document"
        assert FileType.DOCUMENT.value == "document"

    def test_audio_type(self):
        """测试音频文件类型"""
        assert FileType.AUDIO == "audio"
        assert FileType.AUDIO.value == "audio"

    def test_video_type(self):
        """测试视频文件类型"""
        assert FileType.VIDEO == "video"
        assert FileType.VIDEO.value == "video"

    def test_custom_type(self):
        """测试自定义文件类型"""
        assert FileType.CUSTOM == "custom"
        assert FileType.CUSTOM.value == "custom"

    def test_value_of_valid_type(self):
        """测试 value_of 方法获取有效类型"""
        assert FileType.value_of("image") == FileType.IMAGE
        assert FileType.value_of("document") == FileType.DOCUMENT
        assert FileType.value_of("audio") == FileType.AUDIO
        assert FileType.value_of("video") == FileType.VIDEO
        assert FileType.value_of("custom") == FileType.CUSTOM

    def test_value_of_invalid_type_raises(self):
        """测试 value_of 方法对无效类型抛出异常"""
        with pytest.raises(ValueError, match="不存在此文件类型"):
            FileType.value_of("invalid_type")

    def test_all_members_count(self):
        """测试枚举成员数量"""
        members = list(FileType)
        
        assert len(members) == 5

    def test_can_use_as_string(self):
        """测试枚举可以作为字符串使用"""
        file_type = FileType.IMAGE
        
        # StrEnum 允许直接比较字符串
        assert file_type == "image"
        assert f"Type: {file_type}" == "Type: image"

    def test_member_iteration(self):
        """测试枚举成员迭代"""
        members = [member.value for member in FileType]
        
        assert "image" in members
        assert "document" in members
        assert "audio" in members
        assert "video" in members
        assert "custom" in members
