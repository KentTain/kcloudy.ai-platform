"""
站内信发送辅助单元测试
"""
import sys
import types
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from framework.notification.sender import send_notification


def _ensure_notification_mock():
    """确保 iam.models.notification 模块存在（延迟导入 mock）"""
    mock_module = types.ModuleType("iam.models.notification")

    class MockNotification:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    mock_module.Notification = MockNotification

    # 确保 iam 和 iam.models 存在
    if "iam" not in sys.modules:
        sys.modules["iam"] = types.ModuleType("iam")
    if "iam.models" not in sys.modules:
        sys.modules["iam.models"] = types.ModuleType("iam.models")

    sys.modules["iam.models.notification"] = mock_module


@pytest.mark.asyncio
class TestNotificationSender:
    """站内信发送辅助测试"""

    async def test_send_notification_to_users(self):
        """向指定用户列表发送站内信"""
        _ensure_notification_mock()
        session = AsyncMock()
        session.add = MagicMock()

        with patch("framework.notification.sender.get_tenant_id", return_value="tenant-1"), \
             patch("framework.notification.sender.get_user_id", return_value="system"):
            count = await send_notification(
                session=session,
                title="入库审核通知",
                content="您有新的入库申请待审核",
                notification_type="import_review_pending",
                recipient_user_ids=["user-1", "user-2"],
                link="/ai/knowledge-base/1/import-requests/1",
            )

        assert count == 2
        assert session.add.call_count == 2

    async def test_send_notification_empty_recipients(self):
        """空接收人列表返回 0"""
        session = AsyncMock()
        count = await send_notification(
            session=session,
            title="通知",
            content="内容",
            notification_type="test",
            recipient_user_ids=[],
        )
        assert count == 0
        session.add.assert_not_called()
