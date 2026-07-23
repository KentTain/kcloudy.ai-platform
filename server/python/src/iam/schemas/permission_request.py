"""
权限申请相关 Pydantic Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from framework.schemas import BaseModel, BasePaginatedQuery
from pydantic import Field


class PermissionRequestPaginatedQuery(BasePaginatedQuery):
    """权限申请分页查询参数"""

    status: str | None = Field(default=None, description="申请状态")
    request_type: str | None = Field(default=None, description="申请类型")


class PermissionRequestCreate(BaseModel):
    """创建权限申请请求"""

    request_type: str = Field(description="申请类型")
    resource_type: str | None = Field(default=None, description="资源类型")
    resource_id: str | None = Field(default=None, description="资源ID")
    reason: str | None = Field(default=None, description="申请原因")
    target_subject_type: str | None = Field(default=None, description="目标主体类型")
    target_subject_id: str | None = Field(default=None, description="目标主体ID")
    requested_actions: list[str] | None = Field(default=None, description="请求的操作列表")
    request_payload: dict[str, Any] | None = Field(default=None, description="申请附加数据")


class PermissionRequestHandle(BaseModel):
    """处理权限申请请求"""

    result_comment: str | None = Field(default=None, description="审批意见")


class PermissionRequestResponse(BaseModel):
    """权限申请视图对象"""

    id: str
    applicant_id: str = Field(description="申请人ID")
    request_type: str = Field(description="申请类型")
    target_subject_type: str | None = Field(default=None, description="目标主体类型")
    target_subject_id: str | None = Field(default=None, description="目标主体ID")
    resource_type: str | None = Field(default=None, description="资源类型")
    resource_id: str | None = Field(default=None, description="资源ID")
    requested_actions: list[str] | None = Field(default=None, description="请求的操作列表")
    request_payload: dict[str, Any] | None = Field(default=None, description="申请附加数据")
    reason: str | None = Field(default=None, description="申请原因")
    status: str = Field(description="申请状态")
    handler_id: str | None = Field(default=None, description="审批人ID")
    handled_at: datetime | None = Field(default=None, description="审批时间")
    result_comment: str | None = Field(default=None, description="审批意见")
    created_at: datetime = Field(description="创建时间")
