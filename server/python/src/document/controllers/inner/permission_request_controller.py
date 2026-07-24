"""内部接口 - 权限申请回调控制器

供权限申请系统回调，不对外暴露。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.inner import PermissionApplyCallbackRequest
from document.services.member_service import member_service
from document.services.permission_config_service import permission_config_service

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
        if data.request_type == "library_join":
            role = data.requested_role or "member"
            await member_service.add_member(
                session,
                library_id=data.target_resource_id,
                user_id=data.applicant_id,
                user_name=data.applicant_id,
                role=role,
            )
        elif data.request_type == "library_resource":
            action = data.requested_permission or "read"
            await permission_config_service.create_resource_acl(
                session,
                library_id=data.extra_data.get("library_id", ""),
                resource_type=data.extra_data.get("resource_type", "document"),
                resource_id=data.target_resource_id,
                subject_id=data.applicant_id,
                subject_type="user",
                action=action,
            )
        elif data.request_type == "library_role":
            await permission_config_service.add_role_member(
                session,
                library_id=data.extra_data.get("library_id", ""),
                role_id=data.target_resource_id,
                user_id=data.applicant_id,
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的申请类型: {data.request_type}")

        await session.commit()
        return ApiResponse.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
