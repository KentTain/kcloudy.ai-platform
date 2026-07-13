"""Skill 控制器

提供 Skill 调用和预览 API。
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas.skill import SkillInvokeRequest, SkillPreviewResponse
from ai.services.conversation_service import ConversationService
from framework.common.ctx import get_tenant_id, get_user_id
from framework.database.dependencies import get_db_session

router = APIRouter(prefix="/ai/console/v1/skills", tags=["Skills"])

conversation_service = ConversationService()


@router.post("/invoke")
async def invoke_skill(
    request: SkillInvokeRequest,
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """调用 Skill

    支持单个或多个 Skill 组合调用，返回流式响应。

    Args:
        request: 调用请求
        session: 数据库会话

    Returns:
        StreamingResponse: 流式响应
    """
    user_id = get_user_id()
    tenant_id = get_tenant_id()

    async def generate():
        async for chunk in conversation_service.chat_with_skill(
            session=session,
            conversation_id=request.conversation_id,
            user_message=request.user_message,
            skill_ids=request.skill_ids,
            user_id=user_id,
            tenant_id=tenant_id,
        ):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/{skill_id}/preview")
async def preview_skill(
    skill_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """预览 Skill 内容

    返回 Skill 文档和示例，用于前端展示。

    Args:
        skill_id: Skill ID
        session: 数据库会话

    Returns:
        ORJSONResponse: Skill 预览信息
    """
    from tenant.services.plugin_definition_service import (
        plugin_definition_service,
    )
    from tenant.services.plugin_storage_service import plugin_storage_service

    skill_def = await plugin_definition_service.get_by_plugin_id(
        session, skill_id
    )

    if not skill_def or skill_def.plugin_type != "skill":
        raise HTTPException(status_code=404, detail="Skill 不存在")

    # 加载文档
    storage_key = (
        f"skills/global/{skill_id}/{skill_def.local_version}/skill.zip"
    )
    documents = await plugin_storage_service.load_skill_documents(storage_key)

    response = SkillPreviewResponse(
        skill_id=skill_id,
        name=skill_def.name if hasattr(skill_def, "name") else skill_id,
        description=skill_def.declaration.get("metadata", {}).get("description")
        if skill_def.declaration
        else None,
        skill_type=skill_def.skill_type or "knowledge",
        documents=documents,
    )

    return ORJSONResponse(
        content={"code": 200, "msg": "success", "data": response.model_dump()}
    )
