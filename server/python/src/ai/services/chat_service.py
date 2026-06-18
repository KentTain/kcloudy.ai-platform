"""
聊天服务

提供消息相关的业务逻辑封装，包括消息创建、更新等。
"""

import uuid
from datetime import datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.conversation import Conversation
from ai.models.enums import MessageRole, MessageStatus
from ai.models.message import Message

_logger = logger.bind(name=__name__)

# 默认应用配置
DEFAULT_APP_ID = "00000000-0000-0000-0000-000000000001"


class ChatService:
    """聊天服务

    提供消息的聚合方法，封装业务逻辑。
    """

    @staticmethod
    async def create_messages(
        session: AsyncSession,
        tenant_id: str,
        conversation_id: str,
        user_query: str,
        assistant_message_id: str,
        app_id: str = DEFAULT_APP_ID,
    ) -> tuple[Message, Message]:
        """
        创建用户消息和助手消息

        创建一条用户消息和一条状态为 PENDING 的助手消息。

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            conversation_id: 会话 ID
            user_query: 用户问题内容
            assistant_message_id: 助手消息 ID（由调用方生成）
            app_id: 应用 ID，默认为 DEFAULT_APP_ID

        Returns:
            tuple[Message, Message]: (用户消息, 助手消息)
        """
        # 创建用户消息
        user_message = Message(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            app_id=app_id,
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_query,
            status=MessageStatus.COMPLETED,
        )
        session.add(user_message)

        # 创建助手消息（状态为 PENDING）
        assistant_message = Message(
            id=assistant_message_id,
            tenant_id=tenant_id,
            app_id=app_id,
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=None,
            status=MessageStatus.PENDING,
        )
        session.add(assistant_message)

        await session.flush()
        await session.refresh(user_message)
        await session.refresh(assistant_message)

        _logger.info(
            f"创建消息: conversation_id={conversation_id}, "
            f"user_message_id={user_message.id}, "
            f"assistant_message_id={assistant_message.id}"
        )

        return user_message, assistant_message

    @staticmethod
    async def update_assistant_message(
        session: AsyncSession,
        message_id: str,
        content: str,
        status: MessageStatus,
        token_count: int | None = None,
        error_msg: str | None = None,
    ) -> bool:
        """
        更新助手消息

        更新助手消息的内容、状态、Token 数，可选地记录错误信息。

        Args:
            session: 数据库会话
            message_id: 消息 ID
            content: 消息内容
            status: 消息状态
            token_count: Token 数量，可选
            error_msg: 错误信息，可选

        Returns:
            bool: 是否更新成功
        """
        update_data: dict = {
            "content": content,
            "status": status,
        }

        if token_count is not None:
            update_data["token_count"] = token_count

        # 如果有错误信息，记录到 message_metadata
        if error_msg:
            update_data["message_metadata"] = {"error": error_msg}

        await Message.update_by_id(
            session,
            message_id,
            update_data,
        )

        _logger.info(
            f"更新助手消息: message_id={message_id}, status={status}"
        )

        return True

    @staticmethod
    async def update_conversation_name(
        session: AsyncSession,
        conversation_id: str,
        content: str,
    ) -> bool:
        """
        根据对话内容更新会话名称

        如果内容超过 50 字符，截断处理。
        名称格式："对话 {时间}" 或 "对话：{内容前30字}"

        Args:
            session: 数据库会话
            conversation_id: 会话 ID
            content: 对话内容（通常是用户第一条消息）

        Returns:
            bool: 是否更新成功
        """
        # 生成会话名称
        if not content or len(content.strip()) == 0:
            # 内容为空，使用时间格式
            name = f"对话 {datetime.now().strftime('%H:%M')}"
        elif len(content) > 50:
            # 内容超过 50 字符，截取前 30 字符
            truncated = content[:30]
            name = f"对话：{truncated}"
        else:
            # 内容不超过 50 字符，直接使用
            name = f"对话：{content}"

        await Conversation.update_by_id(
            session,
            conversation_id,
            {"name": name},
        )

        _logger.info(f"更新会话名称: conversation_id={conversation_id}, name={name}")

        return True


# 服务单例
chat_service = ChatService()
