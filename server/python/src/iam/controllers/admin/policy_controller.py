"""
企业策略控制器 - 管理端

提供管理端策略 CRUD、启用/停用接口。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.ctx import get_tenant_id, get_user_id
from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from iam.schemas.policy import (
    PolicyCreate,
    PolicyPaginatedQuery,
    PolicyResponse,
    PolicyUpdate,
)
from iam.services.policy_service import policy_service

router = APIRouter()


@router.get("/policies")
async def list_policies(
    query: PolicyPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
):
    """
    管理端查询策略列表

    按当前租户查询，支持分页、关键词、类型、效果、启用状态筛选。
    """
    tenant_id = get_tenant_id()
    items, total = await policy_service.list_policies(
        session,
        tenant_id=tenant_id,
        page=query.page,
        page_size=query.page_size,
        keyword=query.keyword,
        policy_type=query.policy_type,
        effect=query.effect,
        enabled=query.enabled,
    )

    return ApiResponse.paginated(
        data=[PolicyResponse.model_validate(item) for item in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


@router.post("/policies")
async def create_policy(
    data: PolicyCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """
    创建策略

    策略默认停用（enabled=False），需手动启用。
    """
    tenant_id = get_tenant_id()
    user_id = get_user_id()

    policy = await policy_service.create_policy(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        code=data.code,
        name=data.name,
        policy_type=data.policy_type,
        effect=data.effect,
        priority=data.priority,
        enabled=data.enabled,
        condition_json=data.condition_json,
        action_json=data.action_json,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        meta_data=data.meta_data,
    )

    return ApiResponse.success(data=PolicyResponse.model_validate(policy).model_dump())


@router.get("/policies/{policy_id}")
async def get_policy(
    policy_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取策略详情"""
    tenant_id = get_tenant_id()

    policy = await policy_service.get_policy(
        session,
        tenant_id=tenant_id,
        policy_id=policy_id,
    )
    if not policy:
        raise HTTPException(status_code=404, detail="策略不存在")

    return ApiResponse.success(data=PolicyResponse.model_validate(policy).model_dump())


@router.put("/policies/{policy_id}")
async def update_policy(
    policy_id: str,
    data: PolicyUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    """更新策略"""
    tenant_id = get_tenant_id()
    user_id = get_user_id()

    policy = await policy_service.update_policy(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        policy_id=policy_id,
        **data.model_dump(exclude_unset=True),
    )
    if not policy:
        raise HTTPException(status_code=404, detail="策略不存在")

    return ApiResponse.success(data=PolicyResponse.model_validate(policy).model_dump())


@router.delete("/policies/{policy_id}")
async def delete_policy(
    policy_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """删除策略"""
    tenant_id = get_tenant_id()

    deleted = await policy_service.delete_policy(
        session,
        tenant_id=tenant_id,
        policy_id=policy_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="策略不存在")

    return ApiResponse.success(data=None)


@router.put("/policies/{policy_id}/enable")
async def enable_policy(
    policy_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """启用策略"""
    tenant_id = get_tenant_id()
    user_id = get_user_id()

    policy = await policy_service.enable_policy(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        policy_id=policy_id,
    )
    if not policy:
        raise HTTPException(status_code=404, detail="策略不存在")

    return ApiResponse.success(data=PolicyResponse.model_validate(policy).model_dump())


@router.put("/policies/{policy_id}/disable")
async def disable_policy(
    policy_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """停用策略"""
    tenant_id = get_tenant_id()
    user_id = get_user_id()

    policy = await policy_service.disable_policy(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        policy_id=policy_id,
    )
    if not policy:
        raise HTTPException(status_code=404, detail="策略不存在")

    return ApiResponse.success(data=PolicyResponse.model_validate(policy).model_dump())
