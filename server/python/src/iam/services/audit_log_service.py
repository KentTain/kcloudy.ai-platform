"""
审计日志服务

提供审计日志查询功能。
"""

from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.tenant.context import get_tenant_id
from iam.models import AuditLog
from iam.models.enums import AuditLogBusinessType, AuditLogOperationType, AuditLogResourceType
from iam.schemas.audit_log import (
    AuditLogOptionsResponse,
    AuditLogResponse,
    AuditOptionSchema,
)

_logger = logger.bind(name=__name__)


class AuditLogService:
    """审计日志服务"""

    @staticmethod
    async def list_audit_logs(
        session: AsyncSession,
        tenant_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
        business_domain: str | None = None,
        operation_type: str | None = None,
        resource_type: str | None = None,
        operator_by: str | None = None,
        time_range: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[AuditLog], int]:
        """
        获取审计日志列表

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            page: 页码
            page_size: 每页数量
            business_domain: 业务域
            operation_type: 操作类型
            resource_type: 资源类型
            operator_by: 操作人 ID
            time_range: 时间范围（24h/7d/30d/all）
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            tuple[list[AuditLog], int]
        """
        # 构建查询条件
        conditions = []

        # 租户隔离
        if tenant_id:
            conditions.append(AuditLog.tenant_id == tenant_id)

        # 业务域筛选
        if business_domain:
            conditions.append(AuditLog.business_domain == business_domain)

        # 操作类型筛选
        if operation_type:
            conditions.append(AuditLog.operation_type == operation_type)

        # 资源类型筛选
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)

        # 操作人筛选
        if operator_by:
            conditions.append(AuditLog.operator_by == operator_by)

        # 时间范围筛选
        if time_range and time_range != "all":
            now = datetime.now(timezone.utc)
            if time_range == "24h":
                start_time = now - timedelta(hours=24)
            elif time_range == "7d":
                start_time = now - timedelta(days=7)
            elif time_range == "30d":
                start_time = now - timedelta(days=30)

        if start_time:
            conditions.append(AuditLog.operated_at >= start_time)
        if end_time:
            conditions.append(AuditLog.operated_at <= end_time)

        # 查询总数
        count_stmt = select(func.count(AuditLog.id))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = select(AuditLog)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(AuditLog.operated_at.desc()).offset(offset).limit(page_size)

        result = await session.execute(stmt)
        logs = list(result.scalars().all())

        return logs, total

    @staticmethod
    async def get_audit_options(session: AsyncSession) -> AuditLogOptionsResponse:
        """
        获取审计日志选项

        返回业务域、操作类型、资源类型的可选项列表。
        根据当前租户的实际数据动态生成。

        Args:
            session: 数据库会话

        Returns:
            AuditLogOptionsResponse
        """
        tenant_id = get_tenant_id()

        # 查询该租户下实际存在的业务域
        business_domain_stmt = (
            select(AuditLog.business_domain)
            .where(AuditLog.tenant_id == tenant_id)
            .distinct()
        )
        business_domain_result = await session.execute(business_domain_stmt)
        business_domains = [row[0] for row in business_domain_result.all()]

        # 查询该租户下实际存在的操作类型
        operation_type_stmt = (
            select(AuditLog.operation_type)
            .where(AuditLog.tenant_id == tenant_id)
            .distinct()
        )
        operation_type_result = await session.execute(operation_type_stmt)
        operation_types = [row[0] for row in operation_type_result.all()]

        # 查询该租户下实际存在的资源类型
        resource_type_stmt = (
            select(AuditLog.resource_type)
            .where(AuditLog.tenant_id == tenant_id)
            .distinct()
        )
        resource_type_result = await session.execute(resource_type_stmt)
        resource_types = [row[0] for row in resource_type_result.all()]

        # 构建选项响应
        business_domain_options = []
        for domain in business_domains:
            try:
                enum_value = AuditLogBusinessType(domain)
                label = enum_value.label if hasattr(enum_value, "label") else domain
            except ValueError:
                label = domain
            business_domain_options.append(AuditOptionSchema(value=domain, label=label))

        action_options = []
        for action in operation_types:
            try:
                enum_value = AuditLogOperationType(action)
                label = AuditLogOperationType.__labels__.get(action, action)
            except ValueError:
                label = action
            action_options.append(AuditOptionSchema(value=action, label=label))

        resource_type_options = []
        for resource in resource_types:
            try:
                enum_value = AuditLogResourceType(resource)
                label = AuditLogResourceType.__labels__.get(resource, resource)
            except ValueError:
                label = resource
            resource_type_options.append(AuditOptionSchema(value=resource, label=label))

        return AuditLogOptionsResponse(
            business_domains=business_domain_options,
            actions=action_options,
            resource_types=resource_type_options,
        )


# 服务单例
audit_log_service = AuditLogService()
