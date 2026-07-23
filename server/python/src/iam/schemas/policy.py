"""
企业策略相关 Pydantic Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from framework.schemas import BaseModel, BasePaginatedQuery
from pydantic import Field


class PolicyPaginatedQuery(BasePaginatedQuery):
    """策略分页查询参数"""

    keyword: str | None = Field(default=None, description="关键词搜索（编码/名称）")
    policy_type: str | None = Field(default=None, description="策略类型")
    effect: str | None = Field(default=None, description="策略效果")
    enabled: bool | None = Field(default=None, description="是否启用")


class PolicyCreate(BaseModel):
    """创建策略请求"""

    code: str = Field(description="策略编码")
    name: str = Field(description="策略名称")
    policy_type: str = Field(description="策略类型")
    effect: str = Field(default="deny", description="策略效果(allow/deny)")
    priority: int = Field(default=100, description="优先级")
    enabled: bool = Field(default=False, description="是否启用")
    condition_json: dict[str, Any] | None = Field(default=None, description="命中条件")
    action_json: dict[str, Any] | None = Field(default=None, description="动作配置")
    starts_at: datetime | None = Field(default=None, description="生效时间")
    ends_at: datetime | None = Field(default=None, description="失效时间")
    meta_data: dict[str, Any] | None = Field(default=None, description="元数据")


class PolicyUpdate(BaseModel):
    """更新策略请求"""

    code: str | None = Field(default=None, description="策略编码")
    name: str | None = Field(default=None, description="策略名称")
    policy_type: str | None = Field(default=None, description="策略类型")
    effect: str | None = Field(default=None, description="策略效果(allow/deny)")
    priority: int | None = Field(default=None, description="优先级")
    enabled: bool | None = Field(default=None, description="是否启用")
    condition_json: dict[str, Any] | None = Field(default=None, description="命中条件")
    action_json: dict[str, Any] | None = Field(default=None, description="动作配置")
    starts_at: datetime | None = Field(default=None, description="生效时间")
    ends_at: datetime | None = Field(default=None, description="失效时间")
    meta_data: dict[str, Any] | None = Field(default=None, description="元数据")


class PolicyResponse(BaseModel):
    """策略视图对象"""

    id: str
    code: str = Field(description="策略编码")
    name: str = Field(description="策略名称")
    policy_type: str = Field(description="策略类型")
    effect: str = Field(description="策略效果(allow/deny)")
    priority: int = Field(description="优先级")
    enabled: bool = Field(description="是否启用")
    condition_json: dict[str, Any] | None = Field(default=None, description="命中条件")
    action_json: dict[str, Any] | None = Field(default=None, description="动作配置")
    starts_at: datetime | None = Field(default=None, description="生效时间")
    ends_at: datetime | None = Field(default=None, description="失效时间")
    meta_data: dict[str, Any] | None = Field(default=None, description="元数据")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime | None = Field(default=None, description="更新时间")
    created_by: str | None = Field(default=None, description="创建人")
    updated_by: str | None = Field(default=None, description="更新人")
