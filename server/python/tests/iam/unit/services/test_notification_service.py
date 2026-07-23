"""
站内信服务单元测试
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from iam.models import Notification
from iam.services.notification_service import notification_service

# 测试常量
TEST_USER_ID = "user-001"
TEST_TENANT_ID = "tenant-001"


def _build_mock_result(scalars_return=None, scalar_return=None, all_return=None):
    """构建 mock 的 execute 返回值"""
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = scalars_return or []
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar.return_value = scalar_return
    if all_return is not None:
        mock_result.all.return_value = all_return
    return mock_result


def _make_notification(
    id="notif-001",
    title="测试通知",
    recipient_id=TEST_USER_ID,
    notification_type="system",
    is_read=False,
):
    """构造测试用 Notification 实例"""
    return Notification(
        id=id,
        title=title,
        notification_type=notification_type,
        recipient_id=recipient_id,
        tenant_id=TEST_TENANT_ID,
        is_read=is_read,
        content="测试内容",
    )


@pytest.mark.unit
class TestNotificationService:
    """站内信服务测试"""

    @pytest.mark.asyncio
    async def test_list_my_notifications_empty(self, mock_session):
        """
        场景：查询空站内信列表
        WHEN: 用户没有站内信
        THEN: 返回空列表
        """
        mock_session.execute = AsyncMock()
        mock_result_count = _build_mock_result(scalar_return=0)
        mock_result_list = _build_mock_result(scalars_return=[])

        mock_session.execute.side_effect = [mock_result_count, mock_result_list]

        items, total = await notification_service.list_my_notifications(
            mock_session,
            user_id=TEST_USER_ID,
            page=1,
            page_size=20,
        )

        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_list_my_notifications_with_data(self, mock_session):
        """
        场景：查询站内信列表
        WHEN: 用户有站内信
        THEN: 返回站内信列表
        """
        notif = _make_notification()

        mock_result_count = _build_mock_result(scalar_return=1)
        mock_result_list = _build_mock_result(scalars_return=[notif])

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_count, mock_result_list]
        )

        items, total = await notification_service.list_my_notifications(
            mock_session,
            user_id=TEST_USER_ID,
            page=1,
            page_size=20,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0].title == "测试通知"

    @pytest.mark.asyncio
    async def test_list_my_notifications_filter_by_is_read(self, mock_session):
        """
        场景：按已读状态筛选
        WHEN: 指定 is_read=False
        THEN: 返回未读通知
        """
        notif = _make_notification(is_read=False)

        mock_result_count = _build_mock_result(scalar_return=1)
        mock_result_list = _build_mock_result(scalars_return=[notif])

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_count, mock_result_list]
        )

        items, total = await notification_service.list_my_notifications(
            mock_session,
            user_id=TEST_USER_ID,
            page=1,
            page_size=20,
            is_read=False,
        )

        assert total == 1
        assert items[0].is_read is False

    @pytest.mark.asyncio
    async def test_list_my_notifications_filter_by_type(self, mock_session):
        """
        场景：按通知类型筛选
        WHEN: 指定 notification_type
        THEN: 返回匹配类型的通知
        """
        notif = _make_notification(notification_type="permission_request_pending")

        mock_result_count = _build_mock_result(scalar_return=1)
        mock_result_list = _build_mock_result(scalars_return=[notif])

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_count, mock_result_list]
        )

        items, total = await notification_service.list_my_notifications(
            mock_session,
            user_id=TEST_USER_ID,
            page=1,
            page_size=20,
            notification_type="permission_request_pending",
        )

        assert total == 1
        assert items[0].notification_type == "permission_request_pending"

    @pytest.mark.asyncio
    async def test_mark_read(self, mock_session):
        """
        场景：标记站内信已读
        WHEN: 用户标记通知为已读
        THEN: 返回更新数量
        """
        # Mock: execute 返回更新结果
        mock_result = MagicMock()
        mock_result.rowcount = 2
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        count = await notification_service.mark_read(
            mock_session,
            user_id=TEST_USER_ID,
            notification_ids=["notif-001", "notif-002"],
        )

        assert count == 2

    @pytest.mark.asyncio
    async def test_get_unread_count(self, mock_session):
        """
        场景：获取未读数量
        WHEN: 查询未读数
        THEN: 返回正确的未读数量
        """
        mock_result = _build_mock_result(scalar_return=5)
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await notification_service.get_unread_count(
            mock_session,
            user_id=TEST_USER_ID,
        )

        assert count == 5

    @pytest.mark.asyncio
    async def test_get_unread_count_zero(self, mock_session):
        """
        场景：获取未读数量（无未读）
        WHEN: 没有未读通知
        THEN: 返回 0
        """
        mock_result = _build_mock_result(scalar_return=0)
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await notification_service.get_unread_count(
            mock_session,
            user_id=TEST_USER_ID,
        )

        assert count == 0
