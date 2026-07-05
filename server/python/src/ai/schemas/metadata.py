"""元数据 Schema"""

from pydantic import Field

from framework.schemas import BaseModel


class SubmitFeedbackRequest(BaseModel):
    """提交反馈请求"""

    message_id: str = Field(..., description="消息 ID")
    rating: int = Field(..., ge=1, le=2, description="评分：1=👎, 2=👍")
    feedback: str | None = Field(None, max_length=1000, description="反馈文本")


class FeedbackResponse(BaseModel):
    """反馈响应"""

    message_id: str
    rating: int
    feedback: str | None
    created_at: str


class UsageStatsResponse(BaseModel):
    """使用统计响应"""

    total_messages: int
    total_tokens: int
    total_cost: float
    avg_response_time_ms: float
    rating_distribution: dict[int, int]
    model_distribution: dict[str, int]
    period: str