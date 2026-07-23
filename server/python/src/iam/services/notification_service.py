"""
站内信服务

提供站内信查询、标记已读、获取未读数量等功能。
"""

from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import Notification

_logger = logger.bind(name=__name__)


class NotificationService:
    """站内信服务"""

    @staticmethod
    async def list_my_notifications(
        session: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        is_read: bool | None = None,
        notification_type: str | None = None,
    ) -> tuple[list[Notification], int]:
        """
        获取当前用户的站内信列表

        Args:
            session: 数据库会话
            user_id: 用户 ID
            page: 页码
            page_size: 每页数量
            is_read: 是否已读筛选
            notification_type: 通知类型筛选

        Returns:
            tuple[list[Notification], int]
        """
        conditions = [Notification.recipient_id == user_id]

        if is_read is not None:
            conditions.append(Notification.is_read == is_read)

        if notification_type:
            conditions.append(Notification.notification_type == notification_type)

        # 查询总数
        count_stmt = select(func.count(Notification.id)).where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = (
            select(Notification)
            .where(*conditions)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def mark_read(
        session: AsyncSession,
        user_id: str,
        notification_ids: list[str],
    ) -> int:
        """
        标记站内信为已读

        Args:
            session: 数据库会话
            user_id: 用户 ID
            notification_ids: 通知 ID 列表

        Returns:
            int: 更新的记录数
        """
        if not notification_ids:
            return 0

        now = datetime.now(UTC).replace(tzinfo=None)
        stmt = (
            update(Notification)
            .where(
                Notification.id.in_(notification_ids),
                Notification.recipient_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True, read_at=now)
        )

        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount or 0

    @staticmethod
    async def get_unread_count(
        session: AsyncSession,
        user_id: str,
    ) -> int:
        """
        获取当前用户的未读通知数量

        Args:
            session: 数据库会话
            user_id: 用户 ID

        Returns:
            int: 未读数量
        """
        stmt = select(func.count(Notification.id)).where(
            Notification.recipient_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )

        result = await session.execute(stmt)
        return result.scalar() or 0


# 服务单例
notification_service = NotificationService()
