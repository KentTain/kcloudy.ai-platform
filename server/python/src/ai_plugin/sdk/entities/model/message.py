from collections.abc import Sequence
from enum import Enum, StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field, field_validator


class PromptMessageRole(Enum):
    """
    提示消息角色枚举类

    定义对话中不同参与者的角色类型
    """

    SYSTEM = "system"  # 系统角色
    USER = "user"  # 用户角色
    ASSISTANT = "assistant"  # 助手角色
    TOOL = "tool"  # 工具角色

    @classmethod
    def value_of(cls, value: str) -> "PromptMessageRole":
        """
        根据值获取指定的角色

        Args:
            value: 角色值

        Returns:
            PromptMessageRole: 对应的角色枚举

        Raises:
            ValueError: 当角色值无效时抛出
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"无效的提示消息类型值 {value}")


class PromptMessageTool(BaseModel):
    """
    提示消息工具模型类

    定义工具的基本信息和参数
    """

    name: str  # 工具名称
    description: str  # 工具描述
    parameters: dict  # 工具参数，字典中内容如下：{type: "object", properties: {"arg1": {"type": "string", "description": "参数1的描述"}, "arg2": {"type": "number", "description": "参数2的描述"}}}


class PromptMessageFunction(BaseModel):
    """
    提示消息函数模型类

    封装函数调用的相关信息
    """

    type: str = "function"  # 类型，固定为function
    function: PromptMessageTool  # 函数工具


class PromptMessageContentType(StrEnum):
    """
    提示消息内容类型枚举

    定义消息内容支持的媒体类型
    """

    TEXT = "text"  # 文本类型
    IMAGE = "image"  # 图像类型
    AUDIO = "audio"  # 音频类型
    VIDEO = "video"  # 视频类型
    DOCUMENT = "document"  # 文档类型


class PromptMessageContent(BaseModel):
    """
    提示消息内容基类

    所有消息内容类型的基础类
    """

    pass


class TextPromptMessageContent(PromptMessageContent):
    """
    文本提示消息内容模型类

    处理纯文本消息内容
    """

    type: Literal[PromptMessageContentType.TEXT] = (
        PromptMessageContentType.TEXT
    )  # 内容类型
    data: str  # 文本数据


class MultiModalPromptMessageContent(PromptMessageContent):
    """
    多模态提示消息内容模型类

    处理多媒体消息内容的基础类
    """

    format: str = Field(default=..., description="多模态文件的格式")
    base64_data: str = Field(default="", description="多模态文件的base64数据")
    url: str = Field(default="", description="多模态文件的URL")
    mime_type: str = Field(default=..., description="多模态文件的MIME类型")

    @property
    def data(self):
        """
        获取文件数据, base64返回格式：data:image/TYPE;base64,YOUR-BASE64-CONTENT

        Returns:
            str: 文件URL或base64数据URI
        """
        return self.url or f"data:{self.mime_type};base64,{self.base64_data}"


class VideoPromptMessageContent(MultiModalPromptMessageContent):
    """
    视频提示消息内容模型类

    专门处理视频类型的消息内容
    """

    type: Literal[PromptMessageContentType.VIDEO] = PromptMessageContentType.VIDEO


class AudioPromptMessageContent(MultiModalPromptMessageContent):
    """
    音频提示消息内容模型类

    专门处理音频类型的消息内容
    """

    type: Literal[PromptMessageContentType.AUDIO] = PromptMessageContentType.AUDIO


class ImagePromptMessageContent(MultiModalPromptMessageContent):
    """
    图像提示消息内容模型类

    专门处理图像类型的消息内容
    """

    class DETAIL(Enum):
        """
        图像详细度枚举

        定义图像处理的详细程度
        """

        LOW = "low"  # 低详细度
        HIGH = "high"  # 高详细度

    type: Literal[PromptMessageContentType.IMAGE] = (
        PromptMessageContentType.IMAGE
    )  # 内容类型
    detail: DETAIL = DETAIL.LOW  # 详细度，默认为低


class DocumentPromptMessageContent(MultiModalPromptMessageContent):
    """
    文档提示消息内容模型类

    专门处理文档类型的消息内容
    """

    type: Literal[PromptMessageContentType.DOCUMENT] = PromptMessageContentType.DOCUMENT


# 提示消息内容联合类型，支持所有内容类型的区分联合
PromptMessageContentUnionTypes = Annotated[
    TextPromptMessageContent | ImagePromptMessageContent | DocumentPromptMessageContent | AudioPromptMessageContent | VideoPromptMessageContent,
    Field(discriminator="type"),
]


class PromptMessage(BaseModel):
    """
    提示消息模型类

    表示对话中的单条消息
    """

    role: PromptMessageRole  # 消息角色
    content: str | list[PromptMessageContentUnionTypes] | None = None  # 消息内容
    name: str | None = None  # 消息名称（可选）

    def is_empty(self) -> bool:
        """
        检查提示消息是否为空

        Returns:
            bool: 如果消息为空返回True，否则返回False
        """
        return not self.content

    @field_validator("content", mode="before")
    @classmethod
    def transform_content(
        cls,
        value: list[dict]
        | Sequence[PromptMessageContent]
        | list[PromptMessageContent]
        | str
        | None,
    ) -> str | list[PromptMessageContent] | None:
        """
        将内容转换为提示消息内容列表

        Args:
            value: 原始内容值

        Returns:
            Optional[str | list[PromptMessageContent]]: 转换后的内容

        Raises:
            ValueError: 当内容格式无效时抛出
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, Sequence):
            result = []
            for content in value:
                if isinstance(content, PromptMessageContent):
                    result.append(content)
                    continue
                if not isinstance(content, dict):
                    raise ValueError("无效的提示消息内容")
                value_type = content.get("type")
                match value_type:
                    case PromptMessageContentType.TEXT:
                        result.append(TextPromptMessageContent.model_validate(content))
                    case PromptMessageContentType.IMAGE:
                        result.append(ImagePromptMessageContent.model_validate(content))
                    case PromptMessageContentType.AUDIO:
                        result.append(AudioPromptMessageContent.model_validate(content))
                    case PromptMessageContentType.VIDEO:
                        result.append(VideoPromptMessageContent.model_validate(content))
                    case PromptMessageContentType.DOCUMENT:
                        result.append(
                            DocumentPromptMessageContent.model_validate(content)
                        )
                    case _:
                        raise ValueError("无效的提示消息内容类型")
            return result
        return value


class UserPromptMessage(PromptMessage):
    """
    用户提示消息模型类

    表示来自用户的消息
    """

    role: PromptMessageRole = PromptMessageRole.USER  # 角色固定为用户


def _ensure_field_empty_str(value: str | None) -> str:
    """
    确保字段为空字符串而不是None

    Args:
        value: 可选的字符串值

    Returns:
        str: 非None的字符串值
    """
    if value is None:
        return ""
    return value


class AssistantPromptMessage(PromptMessage):
    """
    助手提示消息模型类

    表示来自AI助手的消息，支持工具调用
    """

    class ToolCall(BaseModel):
        """
        助手提示消息工具调用模型类

        表示助手发起的工具调用
        """

        class ToolCallFunction(BaseModel):
            """
            助手提示消息工具调用函数模型类

            表示工具调用的函数信息
            """

            name: Annotated[str, BeforeValidator(_ensure_field_empty_str)]  # 函数名称
            arguments: Annotated[
                str, BeforeValidator(_ensure_field_empty_str)
            ]  # 函数参数

        id: str  # 工具调用ID
        type: Annotated[str, BeforeValidator(_ensure_field_empty_str)]  # 调用类型
        function: ToolCallFunction  # 函数信息

        @field_validator("id", mode="before")
        @classmethod
        def transform_id_to_str(cls, value) -> str:
            """
            将ID转换为字符串

            Args:
                value: ID值

            Returns:
                str: 字符串类型的ID
            """
            if value is None:
                return ""
            elif not isinstance(value, str):
                return str(value)
            else:
                return value

    role: PromptMessageRole = PromptMessageRole.ASSISTANT  # 角色固定为助手
    tool_calls: list[ToolCall] = []  # 工具调用列表

    def is_empty(self) -> bool:
        """
        检查助手提示消息是否为空

        Returns:
            bool: 如果消息和工具调用都为空返回True，否则返回False
        """
        return not (not super().is_empty() and not self.tool_calls)


class SystemPromptMessage(PromptMessage):
    """
    系统提示消息模型类

    表示来自系统的消息，通常包含系统指令
    """

    role: PromptMessageRole = PromptMessageRole.SYSTEM  # 角色固定为系统


class ToolPromptMessage(PromptMessage):
    """
    工具提示消息模型类

    表示来自工具执行的响应消息
    """

    role: PromptMessageRole = PromptMessageRole.TOOL  # 角色固定为工具
    tool_call_id: str  # 工具调用ID

    def is_empty(self) -> bool:
        """
        检查工具提示消息是否为空

        Returns:
            bool: 如果消息内容和工具调用ID都为空返回True，否则返回False
        """
        return not (not super().is_empty() and not self.tool_call_id)
