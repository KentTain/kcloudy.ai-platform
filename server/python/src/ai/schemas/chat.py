"""AI SDK 对话请求 Schema

定义与 Vercel AI SDK 标准格式兼容的 Pydantic Schema。
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from .completion import FileItem, ModelConfig, SearchConfig

# ======================= 消息部分类型 =======================


class TextPart(BaseModel):
    """文本消息部分"""

    type: Literal["text"] = "text"
    text: str = Field(description="文本内容")


class ImagePart(BaseModel):
    """图片消息部分"""

    type: Literal["image"] = "image"
    image: str = Field(description="图片内容（URL 或 base64）")
    mime_type: str | None = Field(None, description="MIME 类型")


class ToolCallPart(BaseModel):
    """工具调用消息部分"""

    type: Literal["tool-call"] = "tool-call"
    tool_call_id: str = Field(description="工具调用 ID")
    tool_name: str = Field(description="工具名称")
    args: dict[str, Any] = Field(default_factory=dict, description="工具参数")


class ToolResultPart(BaseModel):
    """工具结果消息部分"""

    type: Literal["tool-result"] = "tool-result"
    tool_call_id: str = Field(description="工具调用 ID")
    tool_name: str = Field(description="工具名称")
    result: Any = Field(description="工具返回结果")


# UIMessagePart 为 Union 类型，支持多种消息部分
UIMessagePart = TextPart | ImagePart | ToolCallPart | ToolResultPart


# ======================= UI 消息 =======================


class UIMessage(BaseModel):
    """UI 消息 Schema

    与 Vercel AI SDK 的 UIMessage 格式兼容。
    """

    id: str = Field(description="消息 ID")
    role: Literal["user", "assistant", "system"] = Field(description="消息角色")
    parts: list[UIMessagePart] = Field(
        default_factory=list, description="消息部分列表"
    )


# ======================= 请求体配置 =======================


class BodyConfig(BaseModel):
    """请求体配置 Schema

    包含模型配置、搜索配置和文件列表。
    """

    model: ModelConfig = Field(description="模型配置")
    search: SearchConfig | None = Field(None, description="联网搜索配置")
    files: list[FileItem] | None = Field(None, description="上传的文件列表")


# ======================= AI SDK 请求 =======================


class AIChatRequest(BaseModel):
    """AI SDK 对话请求 Schema

    与 Vercel AI SDK 的标准请求格式兼容。
    支持 camelCase 字段名（通过 alias）以匹配前端 JSON 格式。

    示例:
        {
            "id": "conversation-uuid",
            "messages": [
                {"id": "msg-1", "role": "user", "parts": [{"type": "text", "text": "你好"}]}
            ],
            "trigger": "submit-message",
            "messageId": "msg-2",
            "body": {
                "model": {"provider": "openai", "name": "gpt-4", "completionParams": {}}
            }
        }
    """

    id: str | None = Field(None, description="会话 ID，为 None 时表示创建新会话")
    messages: list[UIMessage] = Field(description="消息列表")
    trigger: Literal["submit-message", "regenerate", "edit-message"] = Field(
        description="触发类型：submit-message(发送消息)、regenerate(重新生成)、edit-message(编辑消息)"
    )
    message_id: str = Field(
        alias="messageId",
        description="新消息 ID",
    )
    body: BodyConfig = Field(description="请求体配置")

    model_config = {"populate_by_name": True}
