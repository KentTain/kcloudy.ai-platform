"""AI 模块枚举定义"""

from framework.common.enums import EnumBase


class ConversationStatus(str, EnumBase):
    """会话状态枚举"""
    NORMAL = "normal"
    ARCHIVED = "archived"
    DELETED = "deleted"

    @property
    def label(self) -> str:
        labels = {
            ConversationStatus.NORMAL: "正常",
            ConversationStatus.ARCHIVED: "归档",
            ConversationStatus.DELETED: "已删除",
        }
        return labels.get(self, self.name)


class ConversationMode(str, EnumBase):
    """会话模式枚举"""
    CHAT = "chat"
    COMPLETION = "completion"
    WORKFLOW = "workflow"

    @property
    def label(self) -> str:
        labels = {
            ConversationMode.CHAT: "对话",
            ConversationMode.COMPLETION: "补全",
            ConversationMode.WORKFLOW: "工作流",
        }
        return labels.get(self, self.name)


class MessageStatus(str, EnumBase):
    """消息状态枚举"""
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"

    @property
    def label(self) -> str:
        labels = {
            MessageStatus.PENDING: "等待中",
            MessageStatus.COMPLETED: "已完成",
            MessageStatus.ERROR: "错误",
            MessageStatus.STOPPED: "已停止",
        }
        return labels.get(self, self.name)


class MessageRole(str, EnumBase):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

    @property
    def label(self) -> str:
        labels = {
            MessageRole.USER: "用户",
            MessageRole.ASSISTANT: "助手",
            MessageRole.SYSTEM: "系统",
            MessageRole.TOOL: "工具",
        }
        return labels.get(self, self.name)