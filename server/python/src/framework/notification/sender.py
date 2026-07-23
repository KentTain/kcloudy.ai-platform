"""
站内信发送辅助

延迟导入 iam.models.notification.Notification 避免循环依赖（framework 禁止直接依赖业务模块）。
使用 framework.common.ctx 获取当前请求上下文（租户ID、用户ID）。
"""

from datetime import datetime, timezone

from framework.common.ctx import get_tenant_id, get_user_id


async def send_notification(
    *,
    session,
    title: str,
    content: str,
    notification_type: str,
    recipient_user_ids: list[str],
    link: str | None = None,
) -> int:
    """
    向指定用户列表发送站内信。

    延迟导入 iam.models.notification.Notification，在函数内 import 以避免 framework -> iam 循环依赖。

    Args:
        session: 数据库会话（AsyncSession）
        title: 通知标题
        content: 通知内容
        notification_type: 通知类型（如 import_review_pending）
        recipient_user_ids: 接收人用户ID列表
        link: 关联链接（可选）

    Returns:
        发送数量
    """
    if not recipient_user_ids:
        return 0

    # 延迟导入：避免 framework -> iam 循环依赖
    from iam.models.notification import Notification

    tenant_id = get_tenant_id() or ""
    sender_id = get_user_id() or ""
    now = datetime.now(timezone.utc)

    for user_id in recipient_user_ids:
        notification = Notification(
            tenant_id=tenant_id,
            title=title,
            content=content,
            notification_type=notification_type,
            sender_id=sender_id,
            recipient_id=user_id,
            link=link,
            created_at=now,
        )
        session.add(notification)

    return len(recipient_user_ids)
