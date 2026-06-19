"""LLM 对话补全 Schema

定义 LLM 对话接口的请求和响应 Schema，包括模型配置、搜索配置、文件项和 SSE 事件格式。
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    """模型配置 Schema"""

    provider: str = Field(description="模型提供商")
    name: str = Field(description="模型名称")
    completion_params: dict[str, Any] = Field(
        default_factory=lambda: {"temperature": 0.7},
        description="模型参数，如 temperature、max_tokens 等",
    )


class SearchConfig(BaseModel):
    """搜索配置 Schema"""

    enabled: bool = Field(default=False, description="是否启用联网搜索")
    provider: Literal["baidu"] = Field(default="baidu", description="搜索引擎提供商")


class FileItem(BaseModel):
    """文件项 Schema"""

    type: str = Field(description="文件类型，目前仅支持 image")
    transfer_method: str = Field(
        description="传递方式: remote_url(图片地址) 或 local_file(上传文件)"
    )
    url: str | None = Field(
        None, description="图片地址（仅当传递方式为 remote_url 时）"
    )
    upload_file_id: str | None = Field(
        None, description="上传文件 ID（仅当传递方式为 local_file 时）"
    )

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v != "image":
            raise ValueError("当前仅支持图片格式")
        return v

    @field_validator("transfer_method")
    @classmethod
    def validate_transfer_method(cls, v: str) -> str:
        if v not in ["remote_url", "local_file"]:
            raise ValueError("传递方式必须是 remote_url 或 local_file")
        return v


# SSE 事件 Schema


class SSEMessageData(BaseModel):
    """SSE message 事件数据"""

    content: str = Field(description="对话内容块")


class SSEMessageEvent(BaseModel):
    """SSE message 事件格式"""

    event: Literal["message"] = "message"
    data: SSEMessageData = Field(description="事件数据")


class SSEFinishData(BaseModel):
    """SSE finish 事件数据"""

    prompt_tokens: int = Field(description="提示词 token 数")
    completion_tokens: int = Field(description="补全 token 数")


class SSEFinishEvent(BaseModel):
    """SSE finish 事件格式"""

    event: Literal["finish"] = "finish"
    data: SSEFinishData = Field(description="事件数据")


class SSESearchData(BaseModel):
    """SSE search_keywords 事件数据"""

    keywords: list[str] = Field(description="搜索关键词列表")


class SSESearchEvent(BaseModel):
    """SSE search_keywords 事件格式"""

    event: Literal["search_keywords"] = "search_keywords"
    data: SSESearchData = Field(description="事件数据")


class SSEErrorData(BaseModel):
    """SSE error 事件数据"""

    code: str = Field(description="错误代码")
    message: str = Field(description="错误描述")


class SSEErrorEvent(BaseModel):
    """SSE error 事件格式"""

    event: Literal["error"] = "error"
    data: SSEErrorData = Field(description="事件数据")


# 错误代码常量
class ErrorCode:
    """SSE 错误代码"""

    MODEL_ERROR = "MODEL_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    CONVERSATION_NOT_FOUND = "CONVERSATION_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"


class LLMChatCompletion(BaseModel):
    """LLM 对话补全请求 Schema

    用于简化的对话请求，包含模型配置、查询内容、会话 ID、文件和搜索配置。
    """

    model: ModelConfig = Field(description="模型配置")
    query: str = Field(description="用户查询内容")
    conversation_id: str | None = Field(None, description="会话 ID，为 None 时表示创建新会话")
    files: list[FileItem] | None = Field(None, description="上传的文件列表")
    search: SearchConfig | None = Field(None, description="联网搜索配置")
