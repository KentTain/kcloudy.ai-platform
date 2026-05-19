"""
审计事件

提供数据库操作的审计事件监听。
"""

from datetime import datetime
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from framework.common.ctx import get_user_id, get_tenant_id


class AuditEventListener:
    """审计事件监听器"""

    @staticmethod
    def before_insert(mapper: Any, connection: Any, target: Any) -> None:
        """插入前事件"""
        # 设置创建人
        if hasattr(target, "created_by"):
            user_id = get_user_id()
            if user_id and target.created_by is None:
                target.created_by = user_id

        # 设置租户 ID
        if hasattr(target, "tenant_id"):
            tenant_id = get_tenant_id()
            if tenant_id and target.tenant_id is None:
                target.tenant_id = tenant_id

    @staticmethod
    def before_update(mapper: Any, connection: Any, target: Any) -> None:
        """更新前事件"""
        # 设置更新人
        if hasattr(target, "updated_by"):
            user_id = get_user_id()
            if user_id:
                target.updated_by = user_id


def register_audit_events(base_class: type) -> None:
    """
    注册审计事件监听器

    Args:
        base_class: 基础模型类
    """
    event.listen(base_class, "before_insert", AuditEventListener.before_insert)
    event.listen(base_class, "before_update", AuditEventListener.before_update)
