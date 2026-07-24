"""内部接口 - 权限控制器

供模块间内部调用，不对外暴露。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.services.permission_service import permission_service
from document.services.member_service import member_service

router = APIRouter()


@router.get("/documents/{document_id}/permission")
async def check_document_permission(
    document_id: str,
    user_id: str,
    library_id: str = "",
    operation: str = "read",
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """检查文档权限

    Returns: editable / readonly / none
    """
    result = await permission_service.check_permission(
        session,
        user_id=user_id,
        library_id=library_id,
        resource_type="document",
        resource_id=document_id,
        operation=operation,
    )
    return ApiResponse.success(data={"permission": result})


@router.get("/libraries/{library_id}/members")
async def check_library_member(
    library_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """检查用户是否是文档库成员"""
    member = await member_service.get_member(
        session,
        library_id=library_id,
        user_id=user_id,
    )
    if member:
        return ApiResponse.success(
            data={"is_member": True, "role": member.role}
        )
    return ApiResponse.success(data={"is_member": False, "role": None})
