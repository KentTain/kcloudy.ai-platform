"""用户端文档库成员控制器"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.services.member_service import member_service

router = APIRouter()


class MemberAddRequest(BaseModel):
    """添加成员请求"""

    user_id: str = Field(..., description="用户ID")
    user_name: str = Field(..., description="用户名")
    role: str = Field(default="member", description="角色")
    remarks: str | None = Field(default=None, description="备注")


class MemberRoleUpdate(BaseModel):
    """更新成员角色请求"""

    role: str = Field(..., description="新角色")


class MemberResponse(BaseModel):
    """成员响应"""

    id: str
    library_id: str
    user_id: str
    user_name: str
    role: str
    status: str = "active"
    remarks: str | None = None
    created_at: str | None = None


@router.get("/libraries/{library_id}/members")
async def list_members(
    library_id: str,
    page: int = 1,
    page_size: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查看文档库成员列表"""
    items, total = await member_service.list_members(
        session,
        library_id=library_id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.paginated(
        data=[MemberResponse.model_validate(m).model_dump() for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/libraries/{library_id}/members")
async def add_member(
    library_id: str,
    data: MemberAddRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """添加成员"""
    try:
        member = await member_service.add_member(
            session,
            library_id=library_id,
            user_id=data.user_id,
            user_name=data.user_name,
            role=data.role,
            remarks=data.remarks,
        )
        await session.commit()
        return ApiResponse.success(data=MemberResponse.model_validate(member).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/libraries/{library_id}/members/{user_id}")
async def remove_member(
    library_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """移除成员"""
    try:
        await member_service.remove_member(session, library_id=library_id, user_id=user_id)
        await session.commit()
        return ApiResponse.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/libraries/{library_id}/members/{user_id}/role")
async def update_member_role(
    library_id: str,
    user_id: str,
    data: MemberRoleUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """更新成员角色"""
    try:
        member = await member_service.update_member_role(
            session,
            library_id=library_id,
            user_id=user_id,
            new_role=data.role,
        )
        await session.commit()
        return ApiResponse.success(data=MemberResponse.model_validate(member).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
