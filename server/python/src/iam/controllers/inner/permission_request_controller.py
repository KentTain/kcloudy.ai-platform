"""
权限申请控制器 - 内部接口

提供审批回调 inner 接口（Phase 1 占位）。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from iam.services.permission_request_service import permission_request_service

router = APIRouter()


@router.post("/permission-requests/{request_id}/apply")
async def apply_permission_request(
    request_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    审批回调 inner 接口（Phase 1 占位）

    审批通过后，业务模块调用此接口触发权限生效。
    Phase 1 仅做占位，返回成功响应。
    """
    # Phase 1: 占位实现，后续接入实际权限生效逻辑
    return ApiResponse.success(data={"request_id": request_id, "status": "applied"})
