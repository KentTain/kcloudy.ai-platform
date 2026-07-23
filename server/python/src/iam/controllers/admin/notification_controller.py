"""
站内信控制器 - 管理端

提供管理端站内信查询接口（按租户）。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from framework.tenant.context import get_tenant_id
from iam.schemas.notification import (
    NotificationPaginatedQuery,
    NotificationResponse,
)
from iam.services.notification_service import notification_service

router = APIRouter()


@router.get("/notifications")
async def list_notifications(
    query: NotificationPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    管理端查询站内信列表

    按当前租户查询，支持分页、已读状态、通知类型筛选。
    """
    # 管理端按租户查询，不需要指定 user_id
    items, total = await notification_service.list_my_notifications(
        session,
        user_id="",  # 管理端查询不按用户筛选，返回全部
        page=query.page,
        page_size=query.page_size,
        is_read=query.is_read,
        notification_type=query.notification_type,
    )

    return ApiResponse.paginated(
        data=[NotificationResponse.model_validate(item) for item in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
