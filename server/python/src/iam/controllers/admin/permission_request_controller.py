"""
权限申请控制器 - 管理端

提供管理端权限申请查询接口（按租户）。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from iam.schemas.permission_request import (
    PermissionRequestPaginatedQuery,
    PermissionRequestResponse,
)
from iam.services.permission_request_service import permission_request_service

router = APIRouter()


@router.get("/permission-requests")
async def list_permission_requests(
    query: PermissionRequestPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    管理端查询权限申请列表

    按当前租户查询，支持分页、状态、类型筛选。
    """
    # 管理端查询不按用户筛选，查询所有
    items, total = await permission_request_service.list_my_requests(
        session,
        user_id="",  # 管理端查询全部
        page=query.page,
        page_size=query.page_size,
        status=query.status,
        request_type=query.request_type,
    )

    return ApiResponse.paginated(
        data=[PermissionRequestResponse.model_validate(item) for item in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
