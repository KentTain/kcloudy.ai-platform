"""
Framework 站内信发送辅助

延迟导入 iam.models.notification.Notification 避免循环依赖。
"""

from framework.notification.sender import send_notification

__all__ = [
    "send_notification",
]
