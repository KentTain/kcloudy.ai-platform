"""枚举定义单元测试"""

import pytest

from ai.models.enums import (
    ConversationStatus,
    ConversationMode,
    MessageStatus,
    MessageRole,
)


class TestConversationStatus:
    def test_values(self):
        assert ConversationStatus.NORMAL == "normal"
        assert ConversationStatus.ARCHIVED == "archived"
        assert ConversationStatus.DELETED == "deleted"

    def test_labels(self):
        assert ConversationStatus.NORMAL.label == "正常"
        assert ConversationStatus.ARCHIVED.label == "归档"
        assert ConversationStatus.DELETED.label == "已删除"

    def test_member_count(self):
        assert len(ConversationStatus) == 3


class TestConversationMode:
    def test_values(self):
        assert ConversationMode.CHAT == "chat"
        assert ConversationMode.COMPLETION == "completion"
        assert ConversationMode.WORKFLOW == "workflow"

    def test_labels(self):
        assert ConversationMode.CHAT.label == "对话"
        assert ConversationMode.COMPLETION.label == "补全"
        assert ConversationMode.WORKFLOW.label == "工作流"

    def test_member_count(self):
        assert len(ConversationMode) == 3


class TestMessageStatus:
    def test_values(self):
        assert MessageStatus.PENDING == "pending"
        assert MessageStatus.COMPLETED == "completed"
        assert MessageStatus.ERROR == "error"
        assert MessageStatus.STOPPED == "stopped"

    def test_labels(self):
        assert MessageStatus.PENDING.label == "等待中"
        assert MessageStatus.COMPLETED.label == "已完成"
        assert MessageStatus.ERROR.label == "错误"
        assert MessageStatus.STOPPED.label == "已停止"

    def test_member_count(self):
        assert len(MessageStatus) == 4


class TestMessageRole:
    def test_values(self):
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.TOOL == "tool"

    def test_labels(self):
        assert MessageRole.USER.label == "用户"
        assert MessageRole.ASSISTANT.label == "助手"
        assert MessageRole.SYSTEM.label == "系统"
        assert MessageRole.TOOL.label == "工具"

    def test_member_count(self):
        assert len(MessageRole) == 4