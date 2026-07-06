"""Skill 相关 Schema 定义"""

from __future__ import annotations

from pydantic import Field

from framework.schemas import BaseModel


class SkillInvokeRequest(BaseModel):
    """Skill 调用请求"""

    conversation_id: str = Field(description="对话 ID")
    skill_ids: list[str] = Field(description="Skill ID 列表，支持多个组合调用")
    user_message: str = Field(description="用户消息")


class SkillPreviewResponse(BaseModel):
    """Skill 预览响应"""

    skill_id: str = Field(description="Skill ID")
    name: str = Field(description="Skill 名称")
    description: str | None = Field(default=None, description="Skill 描述")
    skill_type: str = Field(description="Skill 类型：knowledge | script")
    documents: dict[str, str] = Field(
        default_factory=dict, description="Skill 文档内容"
    )


class SkillInvokeChunkResponse(BaseModel):
    """Skill 调用流式响应块"""

    type: str = Field(description="响应类型：chunk | complete | error")
    content: str | None = Field(default=None, description="内容")
    error: str | None = Field(default=None, description="错误信息")
    conversation_id: str | None = Field(default=None, description="对话 ID")
    skill_ids: list[str] | None = Field(default=None, description="Skill ID 列表")
