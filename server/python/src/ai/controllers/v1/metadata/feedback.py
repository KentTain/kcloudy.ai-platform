"""消息反馈控制器

提供消息反馈的提交和更新接口。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas.metadata import FeedbackResponse, SubmitFeedbackRequest
from ai.services.feedback_service import feedback_service
from framework.database.dependencies import get_db_session
from framework.tenant.context import TenantContext
from iam.dependencies import get_current_user_id

router = APIRouter()


@router.post("/feedback")
async def submit_feedback(
    request: SubmitFeedbackRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """提交消息反馈"""

    tenant_id = TenantContext.get_tenant_id()

    # 调用 Service 层处理业务逻辑
    metadata = await feedback_service.submit_feedback(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        request=request,
    )

    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "反馈提交成功",
            "data": FeedbackResponse(
                message_id=metadata.message_id,
                rating=metadata.rating,
                feedback=metadata.feedback,
                created_at=metadata.created_at.isoformat(),
            ).model_dump(),
        }
    )