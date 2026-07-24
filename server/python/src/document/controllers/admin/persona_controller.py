"""管理端人设控制器"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.persona import (
    PersonaCreate,
    PersonaUpdate,
    PersonaPaginatedQuery,
    PersonaResponse,
    PersonaOptionResponse,
)
from document.services.persona_service import persona_service

router = APIRouter()


@router.get("/personas")
async def list_personas(
    query: PersonaPaginatedQuery = Depends(),
    tenant_id: str = "",
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """管理端查看人设列表"""
    items, total = await persona_service.list_personas(
        session,
        tenant_id=tenant_id,
        keyword=query.keyword,
        page=query.page,
        page_size=query.page_size,
    )
    return ApiResponse.paginated(
        data=[PersonaResponse.model_validate(p).model_dump() for p in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


@router.post("/personas")
async def create_persona(
    data: PersonaCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建人设"""
    try:
        persona = await persona_service.create(
            session,
            name=data.name,
            instruction=data.instruction,
            role=data.role,
            description=data.description,
        )
        await session.commit()
        return ApiResponse.success(data=PersonaResponse.model_validate(persona).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/personas/{persona_id}")
async def update_persona(
    persona_id: str,
    data: PersonaUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """更新人设"""
    try:
        persona = await persona_service.update(
            session,
            persona_id=persona_id,
            name=data.name,
            instruction=data.instruction,
            role=data.role,
            description=data.description,
        )
        await session.commit()
        return ApiResponse.success(data=PersonaResponse.model_validate(persona).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/personas/{persona_id}")
async def delete_persona(
    persona_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """删除人设"""
    try:
        await persona_service.delete(session, persona_id)
        await session.commit()
        return ApiResponse.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/personas/options")
async def list_persona_options(
    tenant_id: str = "",
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查看人设选项列表（下拉选择用）"""
    options = await persona_service.list_options(session, tenant_id=tenant_id)
    return ApiResponse.success(data=options)
