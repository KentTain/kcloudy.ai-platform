"""
权限申请控制器 - 用户端

提供权限申请提交、查询、审批等接口。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from iam.dependencies import get_current_user_id, get_current_tenant_id
from iam.schemas.permission_request import (
    PermissionRequestCreate,
    PermissionRequestHandle,
    PermissionRequestPaginatedQuery,
    PermissionRequestResponse,
)
from iam.services.permission_request_service import permission_request_service

router = APIRouter()


@router.post("/permission-requests")
async def submit_request(
    body: PermissionRequestCreate,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
) -> ORJSONResponse:
    """
    提交权限申请
    """
    req = await permission_request_service.submit_request(
        session,
        user_id=user_id,
        tenant_id=tenant_id,
        request_type=body.request_type,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        reason=body.reason,
        target_subject_type=body.target_subject_type,
        target_subject_id=body.target_subject_id,
        requested_actions=body.requested_actions,
        request_payload=body.request_payload,
    )

    return ApiResponse.success(
        data=PermissionRequestResponse.model_validate(req).model_dump()
    )


@router.get("/permission-requests")
async def list_my_requests(
    query: PermissionRequestPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    查询我的权限申请
    """
    items, total = await permission_request_service.list_my_requests(
        session,
        user_id=user_id,
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


@router.get("/permission-requests/pending")
async def list_pending_approvals(
    query: PermissionRequestPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    查询待我审批的权限申请
    """
    items, total = await permission_request_service.list_pending_approvals(
        session,
        user_id=user_id,
        page=query.page,
        page_size=query.page_size,
    )

    return ApiResponse.paginated(
        data=[PermissionRequestResponse.model_validate(item) for item in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


@router.put("/permission-requests/{request_id}/approve")
async def approve_request(
    request_id: str,
    body: PermissionRequestHandle,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    审批通过权限申请
    """
    req = await permission_request_service.approve_request(
        session,
        request_id=request_id,
        handler_id=user_id,
        result_comment=body.result_comment,
    )

    if req is None:
        return ApiResponse.not_found(msg="权限申请不存在")

    return ApiResponse.success(
        data=PermissionRequestResponse.model_validate(req).model_dump()
    )


@router.put("/permission-requests/{request_id}/reject")
async def reject_request(
    request_id: str,
    body: PermissionRequestHandle,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    审批拒绝权限申请
    """
    req = await permission_request_service.reject_request(
        session,
        request_id=request_id,
        handler_id=user_id,
        result_comment=body.result_comment,
    )

    if req is None:
        return ApiResponse.not_found(msg="权限申请不存在")

    return ApiResponse.success(
        data=PermissionRequestResponse.model_validate(req).model_dump()
    )
