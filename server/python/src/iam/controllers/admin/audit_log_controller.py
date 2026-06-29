"""
审计日志控制器 - 管理员端

提供审计日志查询接口。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from framework.tenant.context import get_tenant_id
from iam.schemas.audit_log import (
    AuditLogOptionsResponse,
    AuditLogPaginatedQuery,
    AuditLogResponse,
)
from iam.services.audit_log_service import audit_log_service

router = APIRouter()


@router.get("/audit-logs")
async def list_audit_logs(
    query: AuditLogPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取审计日志列表

    支持分页、业务域、操作类型、资源类型、时间范围筛选。
    """
    tenant_id = get_tenant_id()

    logs, total = await audit_log_service.list_audit_logs(
        session,
        tenant_id=tenant_id,
        page=query.page,
        page_size=query.page_size,
        business_domain=query.business_domain,
        operation_type=query.operation_type,
        resource_type=query.resource_type,
        operator_by=query.operator_by,
        time_range=query.time_range,
        start_time=query.start_time,
        end_time=query.end_time,
    )

    return ApiResponse.paginated(
        data=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


@router.get("/audit-logs/options")
async def get_audit_options(
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取审计日志筛选选项

    返回业务域、操作类型、资源类型的可选项列表。
    """
    options = await audit_log_service.get_audit_options(session)
    return ApiResponse.success(data=options.model_dump())
