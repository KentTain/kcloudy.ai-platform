"""
审计日志相关 Pydantic Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from framework.schemas import BaseModel, BasePaginatedQuery
from pydantic import Field


class AuditLogPaginatedQuery(BasePaginatedQuery):
    """审计日志分页查询参数"""

    business_domain: str | None = Field(default=None, description="业务域")
    operation_type: str | None = Field(default=None, description="操作类型")
    resource_type: str | None = Field(default=None, description="资源类型")
    operator_by: str | None = Field(default=None, description="操作人 ID")
    time_range: str | None = Field(default="7d", description="时间范围：24h/7d/30d/all")
    start_time: datetime | None = Field(default=None, description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")


class AuditLogResponse(BaseModel):
    """审计日志视图对象"""

    id: str
    tenant_id: str
    business_domain: str = Field(description="业务域")
    business_domain_id: str | None = Field(default=None, description="业务域 ID")
    permission_code: str | None = Field(default=None, description="权限编码")
    operator_by: str = Field(description="操作用户 ID")
    operator_name: str = Field(description="操作用户名")
    operated_at: datetime = Field(description="操作时间")
    operation_type: str = Field(description="操作类型")
    resource_type: str = Field(description="资源类型")
    resource_id: str | None = Field(default=None, description="主操作对象 ID")
    resource_name: str = Field(description="主操作对象名称")
    before_data: dict[str, Any] | None = Field(default=None, description="操作前数据")
    after_data: dict[str, Any] | None = Field(default=None, description="操作后数据")
    detail: dict[str, Any] | None = Field(default=None, description="操作详情")
    created_at: datetime = Field(description="创建时间")


class AuditOptionSchema(BaseModel):
    """审计选项"""

    value: str = Field(description="选项值")
    label: str = Field(description="选项标签")


class AuditLogOptionsResponse(BaseModel):
    """审计日志选项响应"""

    business_domains: list[AuditOptionSchema] = Field(
        default_factory=list, description="业务域选项"
    )
    actions: list[AuditOptionSchema] = Field(default_factory=list, description="操作类型选项")
    resource_types: list[AuditOptionSchema] = Field(
        default_factory=list, description="资源类型选项"
    )
