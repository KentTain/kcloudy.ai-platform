from abc import ABC
from collections.abc import Mapping, Sequence
from enum import Enum, StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_serializer, field_validator


class PromptMessageRole(Enum):
    """
    提示消息角色枚举类

    定义对话系统中不同参与者的角色类型
    """

    SYSTEM = "system"  # 系统角色
    USER = "user"  # 用户角色
    ASSISTANT = "assistant"  # 助手角色
    TOOL = "tool"  # 工具角色

    @classmethod
    def value_of(cls, value: str) -> "PromptMessageRole":
        """
        根据字符串值获取对应的角色枚举值

        :param value: 角色值字符串
        :return: 对应的PromptMessageRole枚举值
        :raises ValueError: 当角色值无效时抛出异常
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"无效的提示消息角色值: {value}")


class PromptMessageTool(BaseModel):
    """
    提示消息工具模型类

    定义可供助手调用的工具信息
    """

    name: str  # 工具名称
    description: str  # 工具描述
    parameters: dict  # 工具参数定义


class PromptMessageFunction(BaseModel):
    """
    提示消息函数模型类

    封装函数调用信息，包含函数类型和具体的工具信息
    """

    type: str = "function"  # 函数类型，默认为"function"
    function: PromptMessageTool  # 具体的工具信息


class PromptMessageContentType(StrEnum):
    """
    提示消息内容类型枚举类

    定义消息内容支持的各种媒体类型
    """

    TEXT = "text"  # 文本类型
    IMAGE = "image"  # 图片类型
    AUDIO = "audio"  # 音频类型
    VIDEO = "video"  # 视频类型
    DOCUMENT = "document"  # 文档类型


class PromptMessageContent(ABC, BaseModel):
    """
    提示消息内容抽象基类

    所有消息内容类型的基类，定义了通用的type属性
    """

    type: PromptMessageContentType  # 内容类型


class TextPromptMessageContent(PromptMessageContent):
    """
    文本提示消息内容类

    用于处理纯文本类型的消息内容
    """

    type: Literal[PromptMessageContentType.TEXT] = PromptMessageContentType.TEXT
    data: str  # 文本数据


class MultiModalPromptMessageContent(PromptMessageContent):
    """
    多模态提示消息内容类

    处理多媒体内容的基类，支持base64编码数据和URL两种方式
    """

    format: str = Field(default=..., description="多模态文件的格式")
    base64_data: str = Field(default="", description="多模态文件的base64编码数据")
    url: str = Field(default="", description="多模态文件的URL地址")
    mime_type: str = Field(default=..., description="多模态文件的MIME类型")

    @property
    def data(self):
        """
        获取数据内容，优先返回URL，否则返回base64数据URI

        :return: 数据内容字符串
        """
        return self.url or f"data:{self.mime_type};base64,{self.base64_data}"


class VideoPromptMessageContent(MultiModalPromptMessageContent):
    """视频提示消息内容类"""

    type: Literal[PromptMessageContentType.VIDEO] = PromptMessageContentType.VIDEO


class AudioPromptMessageContent(MultiModalPromptMessageContent):
    """音频提示消息内容类"""

    type: Literal[PromptMessageContentType.AUDIO] = PromptMessageContentType.AUDIO


class ImagePromptMessageContent(MultiModalPromptMessageContent):
    """
    图片提示消息内容类

    处理图片类型的消息内容，支持不同的图片清晰度设置
    """

    class DETAIL(StrEnum):
        """图片清晰度枚举"""

        LOW = "low"  # 低清晰度
        HIGH = "high"  # 高清晰度

    type: Literal[PromptMessageContentType.IMAGE] = PromptMessageContentType.IMAGE
    detail: DETAIL = DETAIL.LOW  # 图片清晰度，默认为低清晰度


class DocumentPromptMessageContent(MultiModalPromptMessageContent):
    """文档提示消息内容类"""

    type: Literal[PromptMessageContentType.DOCUMENT] = PromptMessageContentType.DOCUMENT


# 提示消息内容联合类型，支持类型区分
PromptMessageContentUnionTypes = Annotated[
    TextPromptMessageContent | ImagePromptMessageContent | DocumentPromptMessageContent | AudioPromptMessageContent | VideoPromptMessageContent,
    Field(discriminator="type"),
]


# 内容类型到具体类的映射表
CONTENT_TYPE_MAPPING: Mapping[PromptMessageContentType, type[PromptMessageContent]] = {
    PromptMessageContentType.TEXT: TextPromptMessageContent,
    PromptMessageContentType.IMAGE: ImagePromptMessageContent,
    PromptMessageContentType.AUDIO: AudioPromptMessageContent,
    PromptMessageContentType.VIDEO: VideoPromptMessageContent,
    PromptMessageContentType.DOCUMENT: DocumentPromptMessageContent,
}


class PromptMessage(ABC, BaseModel):
    """
    提示消息抽象基类

    所有消息类型的基类，定义了消息的基本结构
    """

    role: PromptMessageRole  # 消息角色
    content: str | list[PromptMessageContentUnionTypes] | None = None  # 消息内容，可以是字符串或内容列表
    name: str | None = None  # 消息发送者名称（可选）

    def is_empty(self) -> bool:
        """
        检查提示消息是否为空

        :return: 如果消息为空返回True，否则返回False
        """
        return not self.content

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v):
        """
        验证和转换消息内容

        :param v: 待验证的内容
        :return: 验证后的内容
        :raises ValueError: 当内容格式无效时抛出异常
        """
        if isinstance(v, list):
            prompts = []
            for prompt in v:
                if isinstance(prompt, PromptMessageContent):
                    if not isinstance(prompt, TextPromptMessageContent | MultiModalPromptMessageContent):
                        prompt = CONTENT_TYPE_MAPPING[prompt.type].model_validate(prompt.model_dump())
                elif isinstance(prompt, dict):
                    prompt = CONTENT_TYPE_MAPPING[prompt["type"]].model_validate(prompt)
                else:
                    raise ValueError(f"无效的提示消息: {prompt}")
                prompts.append(prompt)
            return prompts
        return v

    @field_serializer("content")
    def serialize_content(
        self, content: str | Sequence[PromptMessageContent] | None
    ) -> str | list[dict[str, Any] | PromptMessageContent] | Sequence[PromptMessageContent] | None:
        """
        序列化消息内容

        :param content: 待序列化的内容
        :return: 序列化后的内容
        """
        if content is None or isinstance(content, str):
            return content
        if isinstance(content, list):
            return [item.model_dump() if hasattr(item, "model_dump") else item for item in content]
        return content


class UserPromptMessage(PromptMessage):
    """
    用户提示消息类

    表示来自用户的消息
    """

    role: PromptMessageRole = PromptMessageRole.USER


class AssistantPromptMessage(PromptMessage):
    """
    助手提示消息类

    表示来自AI助手的消息，可能包含工具调用
    """

    class ToolCall(BaseModel):
        """
        助手工具调用类

        封装助手调用工具的相关信息
        """

        class ToolCallFunction(BaseModel):
            """
            工具调用函数类

            包含具体的函数调用信息
            """

            name: str  # 函数名称
            arguments: str  # 函数参数（JSON字符串）

        id: str  # 工具调用ID
        type: str  # 工具调用类型
        function: ToolCallFunction  # 函数调用信息

        @field_validator("id", mode="before")
        @classmethod
        def transform_id_to_str(cls, value) -> str:
            """
            将ID转换为字符串类型

            :param value: 待转换的值
            :return: 字符串类型的ID
            """
            if not isinstance(value, str):
                return str(value)
            else:
                return value

    role: PromptMessageRole = PromptMessageRole.ASSISTANT
    tool_calls: list[ToolCall] = []  # 工具调用列表

    def is_empty(self) -> bool:
        """
        检查助手消息是否为空

        :return: 如果消息和工具调用都为空返回True，否则返回False
        """
        if not super().is_empty() and not self.tool_calls:
            return False

        return True


class SystemPromptMessage(PromptMessage):
    """
    系统提示消息类

    表示来自系统的消息，通常用于设置对话上下文
    """

    role: PromptMessageRole = PromptMessageRole.SYSTEM


class ToolPromptMessage(PromptMessage):
    """
    工具提示消息类

    表示工具执行结果的消息
    """

    role: PromptMessageRole = PromptMessageRole.TOOL
    tool_call_id: str  # 对应的工具调用ID

    def is_empty(self) -> bool:
        """
        检查工具消息是否为空

        :return: 如果消息内容为空返回True，否则返回False
        """
        return not self.content
