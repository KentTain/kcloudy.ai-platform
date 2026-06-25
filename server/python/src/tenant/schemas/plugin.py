"""
插件定义 Schema

用于管理后台展示插件定义的请求/响应模型。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from framework.schemas import BaseModel, BasePaginatedQuery
from pydantic import Field


# ============== 请求 Schema ==============


class PluginDefinitionQuery(BasePaginatedQuery):
    """插件定义查询请求"""

    type: str | None = Field(default=None, description="安装类型筛选（local/remote）")
    is_recommended: bool | None = Field(default=None, description="是否推荐")
    is_enabled: bool | None = Field(default=None, description="是否启用")


class UpdatePluginDefinitionRequest(BaseModel):
    """更新插件定义请求"""

    is_recommended: bool | None = Field(default=None, description="是否推荐")
    is_enabled: bool | None = Field(default=None, description="是否启用")


class ScanDirectoryRequest(BaseModel):
    """扫描服务器目录请求"""

    directory: str = Field(..., description="服务器目录路径")
    recursive: bool = Field(default=True, description="是否递归扫描子目录")


class UploadPluginRequest(BaseModel):
    """上传插件包请求（用于 API 文档）"""

    overwrite: bool = Field(default=False, description="是否覆盖已存在的插件定义")


class ScannedPluginResult(BaseModel):
    """单个插件扫描结果"""

    plugin_id: str = Field(..., description="插件ID")
    version: str = Field(..., description="版本号")
    status: str = Field(..., description="状态：success/skipped/failed")
    message: str | None = Field(None, description="状态说明或错误信息")


class ScanDirectoryResponse(BaseModel):
    """扫描目录响应"""

    total_count: int = Field(default=0, description="扫描的插件包总数")
    success_count: int = Field(default=0, description="成功注册数")
    skipped_count: int = Field(default=0, description="跳过数（已存在）")
    failed_count: int = Field(default=0, description="失败数")
    results: list[ScannedPluginResult] = Field(default_factory=list, description="扫描结果列表")


class UploadPluginResponse(BaseModel):
    """上传插件包响应"""

    plugin_id: str = Field(..., description="插件ID")
    version: str = Field(..., description="版本号")
    plugin_unique_identifier: str = Field(..., description="插件唯一标识符")
    status: str = Field(..., description="状态：created/updated")
    message: str = Field(..., description="状态说明")


# ============== 响应 Schema ==============


class PluginDefinitionResponse(BaseModel):
    """插件定义列表响应"""

    id: str = Field(..., description="记录ID")
    plugin_id: str = Field(..., description="插件ID，格式：author/name")
    plugin_unique_identifier: str = Field(..., description="插件唯一标识符")
    refers: int = Field(default=0, description="引用租户数")
    install_type: str = Field(..., description="安装类型（local/remote）")
    manifest_type: str | None = Field(None, description="清单类型")
    is_recommended: bool = Field(default=False, description="是否推荐")
    is_enabled: bool = Field(default=True, description="是否启用")
    created_at: datetime | None = Field(None, description="创建时间")
    updated_at: datetime | None = Field(None, description="更新时间")


class PluginDefinitionPaginatedResponse(BaseModel):
    """插件定义分页列表响应"""

    items: list[PluginDefinitionResponse] = Field(default_factory=list, description="插件定义列表")
    total: int = Field(default=0, description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页条数")


class PluginDefinitionDetailResponse(BaseModel):
    """插件定义详情响应"""

    id: str = Field(..., description="记录ID")
    plugin_id: str = Field(..., description="插件ID，格式：author/name")
    plugin_unique_identifier: str = Field(..., description="插件唯一标识符")
    declaration: dict[str, Any] = Field(default_factory=dict, description="完整声明内容")
    refers: int = Field(default=0, description="引用租户数")
    install_type: str = Field(..., description="安装类型（local/remote）")
    manifest_type: str | None = Field(None, description="清单类型")
    is_recommended: bool = Field(default=False, description="是否推荐")
    is_enabled: bool = Field(default=True, description="是否启用")
    created_at: datetime | None = Field(None, description="创建时间")
    updated_at: datetime | None = Field(None, description="更新时间")


# ─────────────────────────────────────────────────────────────────────────────
# 统计仪表板 Schema
# ─────────────────────────────────────────────────────────────────────────────


class DefinitionStats(BaseModel):
    """插件定义统计数据"""

    total_count: int = Field(..., description="插件定义总数")
    by_type: dict[str, int] = Field(
        default_factory=dict, description="按安装类型分布，如 {\"local\": 10, \"remote\": 5}"
    )
    recommended_count: int = Field(..., description="推荐插件数")
    enabled_count: int = Field(..., description="启用插件数")


class InstallationStats(BaseModel):
    """插件安装统计数据"""

    total_count: int = Field(..., description="总安装次数")
    active_count: int = Field(..., description="活跃安装数（状态为 ACTIVE）")
    weekly_new_count: int = Field(..., description="本周新增安装数")


class PluginStatisticsResponse(BaseModel):
    """插件统计响应"""

    definition_stats: DefinitionStats = Field(..., description="插件定义统计")
    installation_stats: InstallationStats = Field(..., description="插件安装统计")
    cached_at: datetime | None = Field(None, description="缓存时间（如果使用缓存）")
