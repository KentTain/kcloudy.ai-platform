"""
会话服务

提供会话的业务逻辑封装，包括列表查询、创建恢复、软删除等。
"""

import uuid
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.conversation import Conversation
from ai.models.enums import ConversationStatus, ConversationMode
from ai.models.message import Message
from ai.schemas.conversation import ConversationListItem

_logger = logger.bind(name=__name__)

# 默认应用配置
DEFAULT_APP_ID = "00000000-0000-0000-0000-000000000001"


class ConversationService:
    """会话服务

    提供会话的聚合方法，封装业务逻辑。
    """

    @staticmethod
    async def list_with_message_count(
        session: AsyncSession,
        tenant_id: str,
    ) -> list[ConversationListItem]:
        """
        查询会话列表并统计每个会话的消息数量

        Args:
            session: 数据库会话
            tenant_id: 租户 ID

        Returns:
            list[ConversationListItem]: 会话列表项
        """
        # 使用子查询统计消息数量
        message_count_subquery = (
            select(
                Message.conversation_id,
                func.count(Message.id).label("count"),
            )
            .where(Message.tenant_id == tenant_id)
            .group_by(Message.conversation_id)
            .subquery()
        )

        # 查询会话列表
        stmt = (
            select(
                Conversation.id,
                Conversation.name,
                Conversation.created_at,
                func.coalesce(message_count_subquery.c.count, 0).label("message_count"),
            )
            .outerjoin(
                message_count_subquery,
                Conversation.id == message_count_subquery.c.conversation_id,
            )
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.status != ConversationStatus.DELETED,
            )
            .order_by(Conversation.created_at.desc())
        )

        result = await session.execute(stmt)
        rows = result.all()

        return [
            ConversationListItem(
                id=str(row.id),
                name=row.name,
                created_at=row.created_at,
                message_count=row.message_count,
            )
            for row in rows
        ]

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        conversation_id: str,
        tenant_id: str,
    ) -> Conversation | None:
        """
        根据 ID 获取会话

        Args:
            session: 数据库会话
            conversation_id: 会话 ID
            tenant_id: 租户 ID

        Returns:
            Conversation | None: 会话对象，不存在则返回 None
        """
        return await Conversation.one_by_conditions(
            session,
            conditions=[
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            ],
        )

    @staticmethod
    async def get_or_create(
        session: AsyncSession,
        conversation_id: str | None,
        tenant_id: str,
        user_id: str,
        app_id: str | None = None,
    ) -> tuple[Conversation, bool]:
        """
        获取或创建会话

        如果 conversation_id 为 None，创建新会话。
        如果 conversation_id 存在，检查并返回已有会话或创建新会话。

        Args:
            session: 数据库会话
            conversation_id: 会话 ID，None 表示创建新会话
            tenant_id: 租户 ID
            user_id: 用户 ID
            app_id: 应用 ID，可选

        Returns:
            tuple[Conversation, bool]: (会话对象, 是否新创建)
        """
        effective_app_id = app_id or DEFAULT_APP_ID

        # 如果未提供 conversation_id，创建新会话
        if conversation_id is None:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                app_id=effective_app_id,
                name="新对话",
                status=ConversationStatus.NORMAL,
                mode=ConversationMode.CHAT,
            )
            session.add(conversation)
            await session.flush()
            await session.refresh(conversation)
            _logger.info(f"创建新会话: {conversation.id}")
            return conversation, True

        # 检查会话是否已存在
        existing = await Conversation.one_by_conditions(
            session,
            conditions=[
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            ],
        )

        if existing:
            return existing, False

        # 会话不存在，创建新会话（使用指定的 ID）
        conversation = Conversation(
            id=conversation_id,
            tenant_id=tenant_id,
            app_id=effective_app_id,
            name="新对话",
            status=ConversationStatus.NORMAL,
            mode=ConversationMode.CHAT,
        )
        session.add(conversation)
        await session.flush()
        await session.refresh(conversation)
        _logger.info(f"创建新会话: {conversation.id}")
        return conversation, True

    @staticmethod
    async def soft_delete(
        session: AsyncSession,
        conversation_id: str,
        tenant_id: str,
    ) -> bool:
        """
        软删除会话

        将会话状态设为 DELETED。

        Args:
            session: 数据库会话
            conversation_id: 会话 ID
            tenant_id: 租户 ID

        Returns:
            bool: 是否删除成功
        """
        conversation = await Conversation.one_by_conditions(
            session,
            conditions=[
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            ],
        )

        if not conversation:
            return False

        conversation.status = ConversationStatus.DELETED
        _logger.info(f"软删除会话: {conversation_id}")
        return True

    @staticmethod
    async def update_name(
        session: AsyncSession,
        conversation_id: str,
        name: str,
    ) -> bool:
        """
        更新会话名称

        Args:
            session: 数据库会话
            conversation_id: 会话 ID
            name: 新名称

        Returns:
            bool: 是否更新成功
        """
        await Conversation.update_by_id(
            session,
            conversation_id,
            {"name": name},
        )
        _logger.info(f"更新会话名称: {conversation_id} -> {name}")
        return True


# 服务单例
conversation_service = ConversationService()
