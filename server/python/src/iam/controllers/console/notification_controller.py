"""
站内信控制器 - 用户端

提供站内信查询、标记已读、未读数量等接口。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from iam.dependencies import get_current_user_id, get_current_tenant_id
from iam.schemas.notification import (
    NotificationMarkReadRequest,
    NotificationPaginatedQuery,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from iam.services.notification_service import notification_service

router = APIRouter()


@router.get("/notifications")
async def list_my_notifications(
    query: NotificationPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    获取我的站内信列表

    支持分页、已读状态、通知类型筛选。
    """
    items, total = await notification_service.list_my_notifications(
        session,
        user_id=user_id,
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


@router.get("/notifications/unread-count")
async def get_unread_count(
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    获取未读通知数量
    """
    count = await notification_service.get_unread_count(
        session,
        user_id=user_id,
    )

    return ApiResponse.success(
        data=NotificationUnreadCountResponse(unread_count=count).model_dump()
    )


@router.put("/notifications/read")
async def mark_read(
    body: NotificationMarkReadRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    标记站内信为已读
    """
    count = await notification_service.mark_read(
        session,
        user_id=user_id,
        notification_ids=body.notification_ids,
    )

    return ApiResponse.success(data={"updated_count": count})
