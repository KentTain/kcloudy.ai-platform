"""
站内信控制器单元测试
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from iam.models import Notification


def _make_notification(
    id="notif-001",
    title="测试通知",
    recipient_id="user-001",
    notification_type="system",
    is_read=False,
):
    """构造测试用 Notification 实例"""
    return Notification(
        id=id,
        title=title,
        notification_type=notification_type,
        recipient_id=recipient_id,
        tenant_id="tenant-001",
        is_read=is_read,
        content="测试内容",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _parse_response(result):
    """解析 ORJSONResponse"""
    return json.loads(result.body)


@pytest.mark.unit
class TestConsoleNotificationController:
    """Console 站内信控制器测试"""

    @pytest.mark.asyncio
    async def test_list_my_notifications(self, mock_session):
        """
        场景：查询我的站内信
        WHEN: 调用 list_my_notifications 接口
        THEN: 返回分页数据
        """
        from iam.controllers.console.notification_controller import (
            list_my_notifications,
        )
        from iam.schemas.notification import NotificationPaginatedQuery

        notif = _make_notification()

        with patch(
            "iam.services.notification_service.notification_service.list_my_notifications",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = ([notif], 1)

            query = NotificationPaginatedQuery(page=1, page_size=20)
            result = await list_my_notifications(
                query=query,
                session=mock_session,
                user_id="user-001",
            )

            assert result.status_code == 200
            body = _parse_response(result)
            assert body["code"] == 200
            assert body["data"] is not None

    @pytest.mark.asyncio
    async def test_get_unread_count(self, mock_session):
        """
        场景：获取未读数量
        WHEN: 调用 get_unread_count 接口
        THEN: 返回未读数
        """
        from iam.controllers.console.notification_controller import (
            get_unread_count,
        )

        with patch(
            "iam.services.notification_service.notification_service.get_unread_count",
            new_callable=AsyncMock,
        ) as mock_count:
            mock_count.return_value = 3

            result = await get_unread_count(
                session=mock_session,
                user_id="user-001",
            )

            assert result.status_code == 200
            body = _parse_response(result)
            assert body["data"]["unread_count"] == 3

    @pytest.mark.asyncio
    async def test_mark_read(self, mock_session):
        """
        场景：标记已读
        WHEN: 调用 mark_read 接口
        THEN: 返回更新数量
        """
        from iam.controllers.console.notification_controller import mark_read
        from iam.schemas.notification import NotificationMarkReadRequest

        with patch(
            "iam.services.notification_service.notification_service.mark_read",
            new_callable=AsyncMock,
        ) as mock_mark:
            mock_mark.return_value = 2

            req = NotificationMarkReadRequest(
                notification_ids=["notif-001", "notif-002"]
            )
            result = await mark_read(
                body=req,
                session=mock_session,
                user_id="user-001",
            )

            assert result.status_code == 200
            body = _parse_response(result)
            assert body["data"]["updated_count"] == 2


@pytest.mark.unit
class TestAdminNotificationController:
    """Admin 站内信控制器测试"""

    @pytest.mark.asyncio
    async def test_list_notifications(self, mock_session):
        """
        场景：管理端查询站内信
        WHEN: 调用 list_notifications 接口
        THEN: 返回分页数据
        """
        from iam.controllers.admin.notification_controller import (
            list_notifications,
        )
        from iam.schemas.notification import NotificationPaginatedQuery

        notif = _make_notification()

        with patch(
            "iam.services.notification_service.notification_service.list_my_notifications",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = ([notif], 1)

            query = NotificationPaginatedQuery(page=1, page_size=20)
            result = await list_notifications(
                query=query,
                session=mock_session,
            )

            assert result.status_code == 200
            body = _parse_response(result)
            assert body["code"] == 200
