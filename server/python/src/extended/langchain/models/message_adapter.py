"""
Message adapter for LangChain <-> Platform message conversion

Provides bidirectional conversion between LangChain BaseMessage
and platform PromptMessage types.
"""

from __future__ import annotations

from collections.abc import Sequence

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from ai_plugin.sdk.entities.model.message import (
    AssistantPromptMessage,
    ImagePromptMessageContent,
    PromptMessage,
    SystemPromptMessage,
    TextPromptMessageContent,
    UserPromptMessage,
)


class UnsupportedMessageTypeError(TypeError):
    """Raised when an unsupported message type is encountered."""

    def __init__(self, message_type: str) -> None:
        self.message_type = message_type
        super().__init__(f"Unsupported message type: {message_type}")


def _lc_content_to_platform(
    content: str | list[str | dict] | None,
) -> str | Sequence[TextPromptMessageContent | ImagePromptMessageContent] | None:
    """Convert LangChain content to platform PromptMessage content.

    - str / None passes through
    - list[str | dict] is mapped to list[TextPromptMessageContent | ImagePromptMessageContent]
    """
    if content is None or isinstance(content, str):
        return content
    result: list[TextPromptMessageContent | ImagePromptMessageContent] = []
    for item in content:
        if isinstance(item, str):
            result.append(TextPromptMessageContent(data=item))
        elif isinstance(item, dict):
            match item.get("type"):
                case "text":
                    result.append(TextPromptMessageContent(data=item.get("text", "")))
                case "image_url":
                    url = (item.get("image_url") or {}).get("url", "")
                    result.append(
                        ImagePromptMessageContent(
                            format="url",
                            url=url,
                            mime_type="image/png",
                        )
                    )
                case _:
                    # Fallback: serialize dict as text
                    result.append(TextPromptMessageContent(data=str(item)))
    return result


def _platform_content_to_lc(
    content: str | list | None,
) -> str | list[str | dict] | None:
    """Convert platform PromptMessage content to LangChain content.

    - str / None passes through
    - list[PromptMessageContent] is mapped to list[str | dict]
    """
    if content is None or isinstance(content, str):
        return content
    result: list[str | dict] = []
    for item in content:
        if isinstance(item, TextPromptMessageContent):
            result.append(item.data)
        elif isinstance(item, ImagePromptMessageContent):
            url = item.url or item.data
            result.append({"type": "image_url", "image_url": {"url": url}})
        elif isinstance(item, str) or isinstance(item, dict):
            result.append(item)
        else:
            result.append(str(item))
    return result


class MessageAdapter:
    """Bidirectional converter between LangChain and platform messages."""

    @staticmethod
    def to_platform_message(message: BaseMessage) -> PromptMessage:
        """Convert a LangChain message to a platform PromptMessage."""
        content = _lc_content_to_platform(message.content)
        match message:
            case HumanMessage():
                return UserPromptMessage(content=content)
            case AIMessage():
                return AssistantPromptMessage(content=content)
            case SystemMessage():
                return SystemPromptMessage(content=content)
            case _:
                raise UnsupportedMessageTypeError(type(message).__name__)

    @staticmethod
    def to_platform_messages(messages: list[BaseMessage]) -> list[PromptMessage]:
        """Convert a list of LangChain messages to platform PromptMessages."""
        return [MessageAdapter.to_platform_message(m) for m in messages]

    @staticmethod
    def to_langchain_message(message: PromptMessage) -> BaseMessage:
        """Convert a platform PromptMessage to a LangChain message."""
        content = _platform_content_to_lc(message.content)
        match message:
            case UserPromptMessage():
                return HumanMessage(content=content)
            case AssistantPromptMessage():
                return AIMessage(content=content)
            case SystemPromptMessage():
                return SystemMessage(content=content)
            case _:
                raise UnsupportedMessageTypeError(type(message).__name__)
