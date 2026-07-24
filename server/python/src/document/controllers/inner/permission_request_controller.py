"""内部接口 - 权限申请回调控制器

供权限申请系统回调，不对外暴露。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.inner import PermissionApplyCallbackRequest
from document.services.permission_request_service import permission_request_service

router = APIRouter()


@router.post("/permission-requests/{request_id}/apply")
async def apply_permission_request(
    request_id: str,
    data: PermissionApplyCallbackRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """处理权限申请回调

    根据申请类型执行对应的授权操作：
    - library_join: 将用户添加为文档库成员
    - library_resource: 为用户创建资源 ACL
    - library_role: 将用户添加到权限组
    """
    try:
        await permission_request_service.apply_callback(
            session,
            request_type=data.request_type,
            target_resource_id=data.target_resource_id,
            applicant_id=data.applicant_id,
            requested_role=data.requested_role,
            requested_permission=data.requested_permission,
            extra_data=data.extra_data,
        )
        await session.commit()
        return ApiResponse.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
