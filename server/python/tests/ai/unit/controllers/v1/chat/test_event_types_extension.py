import pytest
from ai.controllers.v1.chat.event_types import EventType


class TestEventTypeExtension:
    def test_source_events_exist(self):
        """测试来源事件类型存在"""
        assert hasattr(EventType, "SOURCE_URL")
        assert hasattr(EventType, "SOURCE_DOCUMENT")
        assert EventType.SOURCE_URL == "source-url"
        assert EventType.SOURCE_DOCUMENT == "source-document"

    def test_file_events_exist(self):
        """测试文件事件类型存在"""
        assert hasattr(EventType, "FILE_UPLOAD_START")
        assert hasattr(EventType, "FILE_UPLOAD_END")
        assert EventType.FILE_UPLOAD_START == "file-upload-start"
        assert EventType.FILE_UPLOAD_END == "file-upload-end"

    def test_data_event_exists(self):
        """测试数据事件类型存在"""
        assert hasattr(EventType, "DATA")
        assert EventType.DATA == "data"

    def test_warning_event_exists(self):
        """测试警告事件类型存在"""
        assert hasattr(EventType, "WARNING")
        assert EventType.WARNING == "warning"
