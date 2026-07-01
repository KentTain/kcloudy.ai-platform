"""
审计服务

提供审计日志记录核心逻辑。
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from framework.audit.context import AuditContext
from framework.audit.templates import AuditTemplateBuilder
from framework.common.ctx import get_context, get_permission_code, get_tenant_id, get_user_id
from iam.models import AuditLog


class AuditService:
    """审计服务"""

    def __init__(self):
        self.template_builder = AuditTemplateBuilder()

    async def record(
        self,
        session: AsyncSession,
        context: AuditContext,
    ) -> None:
        """
        记录审计日志

        Args:
            session: 数据库会话（由调用方管理事务）
            context: 审计上下文
        """
        user_id = get_user_id()
        user_name = get_user_name()
        tenant_id = get_tenant_id()
        permission_code = get_permission_code()

        operated_at = datetime.now(timezone.utc)
        operated_at_str = operated_at.strftime("%Y-%m-%d %H:%M:%S")

        detail = self.template_builder.build_detail(
            module=context.module,
            resource=context.resource,
            action=context.action,
            operator_name=user_name or "",
            operated_at=operated_at_str,
            resource_name=context.resource_name,
            extra=context.detail_extra,
        )

        audit_log = AuditLog(
            tenant_id=tenant_id,
            business_domain=context.module,
            operation_type=context.action,
            resource_type=context.resource,
            resource_id=context.resource_id,
            resource_name=context.resource_name,
            permission_code=permission_code,
            operator_by=user_id,
            operator_name=user_name or "",
            operated_at=operated_at,
            before_data=context.before_data,
            after_data=context.after_data,
            detail=detail,
        )

        session.add(audit_log)

    def _get_user_name(self) -> str | None:
        """获取当前用户名称"""
        return get_user_name()


def get_user_name() -> str | None:
    """获取当前用户名称"""
    ctx = get_context()
    return ctx.user_name


audit_service = AuditService()
