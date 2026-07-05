# src/ai/controllers/v1/metadata/stats.py
"""使用统计控制器

提供使用统计数据的查询接口。
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import ORJSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.message_metadata import MessageMetadata
from ai.schemas.metadata import UsageStatsResponse
from framework.database.dependencies import get_db_session
from framework.tenant.context import TenantContext

router = APIRouter()


@router.get("/usage-stats")
async def get_usage_stats(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取使用统计"""

    tenant_id = TenantContext.get_tenant_id()

    # 默认查询最近 30 天
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    # 查询统计数据
    result = await session.execute(
        select(
            func.count(MessageMetadata.id).label("total_messages"),
            func.sum(MessageMetadata.total_tokens).label("total_tokens"),
            func.avg(MessageMetadata.response_time_ms).label("avg_response_time"),
        ).where(
            MessageMetadata.tenant_id == tenant_id,
            MessageMetadata.created_at >= start_date,
            MessageMetadata.created_at <= end_date,
        )
    )
    stats = result.one()

    # 评分分布
    rating_result = await session.execute(
        select(
            MessageMetadata.rating,
            func.count(MessageMetadata.id).label("count"),
        ).where(
            MessageMetadata.tenant_id == tenant_id,
            MessageMetadata.created_at >= start_date,
            MessageMetadata.created_at <= end_date,
            MessageMetadata.rating.isnot(None),
        ).group_by(MessageMetadata.rating)
    )
    rating_distribution = {row.rating: row.count for row in rating_result}

    # 模型分布
    model_result = await session.execute(
        select(
            MessageMetadata.model_name,
            func.count(MessageMetadata.id).label("count"),
        ).where(
            MessageMetadata.tenant_id == tenant_id,
            MessageMetadata.created_at >= start_date,
            MessageMetadata.created_at <= end_date,
            MessageMetadata.model_name.isnot(None),
        ).group_by(MessageMetadata.model_name)
    )
    model_distribution = {row.model_name: row.count for row in model_result}

    # 计算成本（假设平均成本 $5/1M tokens）
    total_cost = ((stats.total_tokens or 0) / 1_000_000) * 5.0

    return ORJSONResponse(
        content={
            "code": 200,
            "data": UsageStatsResponse(
                total_messages=stats.total_messages or 0,
                total_tokens=stats.total_tokens or 0,
                total_cost=total_cost,
                avg_response_time_ms=float(stats.avg_response_time or 0),
                rating_distribution=rating_distribution,
                model_distribution=model_distribution,
                period=f"{start_date} ~ {end_date}",
            ).model_dump(),
        }
    )
