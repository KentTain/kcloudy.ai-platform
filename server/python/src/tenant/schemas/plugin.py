"""
插件定义 Schema

用于管理后台展示插件定义的请求/响应模型。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

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
    install_type: str | None = Field(None, description="安装类型（local/remote）")
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
    install_type: str | None = Field(None, description="安装类型（local/remote）")
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


# ─────────────────────────────────────────────────────────────────────────────
# 预览功能 Schema
# ─────────────────────────────────────────────────────────────────────────────


class ScannedPluginPreview(BaseModel):
    """扫描预览结果"""

    plugin_id: str = Field(..., description="插件ID")
    version: str = Field(..., description="版本号")
    name: str = Field(..., description="插件名称")
    description: str | None = Field(default=None, description="插件描述")
    exists: bool = Field(default=False, description="是否已存在")
    status: Literal["ready", "invalid"] = Field(default="ready", description="状态：ready=可导入，invalid=解析失败")
    error_message: str | None = Field(None, description="错误信息")


class ParsedPluginInfo(BaseModel):
    """解析插件结果"""

    plugin_id: str = Field(..., description="插件ID")
    version: str = Field(..., description="版本号")
    name: str = Field(..., description="插件名称")
    description: str | None = Field(default=None, description="插件描述")
    manifest_type: str | None = Field(None, description="清单类型")
    declaration: dict[str, Any] = Field(default_factory=dict, description="完整声明内容")
    exists: bool = Field(default=False, description="是否已存在")


class ScanDirectoryConfirmRequest(BaseModel):
    """扫描确认请求"""

    directory: str = Field(..., description="服务器目录路径")
    recursive: bool = Field(default=False, description="是否递归扫描子目录")
    plugin_ids: list[str] = Field(default_factory=list, description="指定要导入的插件ID列表")


# ─────────────────────────────────────────────────────────────────────────────
# 安装到租户 Schema
# ─────────────────────────────────────────────────────────────────────────────


class InstallToTenantsRequest(BaseModel):
    """安装插件到租户请求"""

    tenant_ids: list[str] = Field(..., min_length=1, description="目标租户ID列表")
    auto_start: bool = Field(default=False, description="是否自动启动")


class InstallSuccessItem(BaseModel):
    """安装成功项"""

    tenant_id: str = Field(..., description="租户ID")
    plugin_id: str = Field(..., description="插件ID")


class InstallFailedItem(BaseModel):
    """安装失败项"""

    tenant_id: str = Field(..., description="租户ID")
    message: str = Field(..., description="错误信息")


class InstallSkippedItem(BaseModel):
    """安装跳过项"""

    tenant_id: str = Field(..., description="租户ID")
    reason: str = Field(..., description="跳过原因")


class InstallToTenantsResponse(BaseModel):
    """安装插件到租户响应"""

    success: list[InstallSuccessItem] = Field(default_factory=list, description="成功列表")
    failed: list[InstallFailedItem] = Field(default_factory=list, description="失败列表")
    skipped: list[InstallSkippedItem] = Field(default_factory=list, description="跳过列表")


# ─────────────────────────────────────────────────────────────────────────────
# 插件启停 Schema
# ─────────────────────────────────────────────────────────────────────────────


class BatchStartStopRequest(BaseModel):
    """批量启停插件请求"""

    plugin_id: str = Field(..., description="插件ID")
    tenant_ids: list[str] = Field(..., min_length=1, description="目标租户ID列表")


class BatchOperationItem(BaseModel):
    """批量操作成功项"""

    tenant_id: str = Field(..., description="租户ID")
    plugin_id: str = Field(..., description="插件ID")
    status: str = Field(..., description="操作后状态")


class BatchOperationFailedItem(BaseModel):
    """批量操作失败项"""

    tenant_id: str = Field(..., description="租户ID")
    plugin_id: str = Field(..., description="插件ID")
    error: str = Field(..., description="错误信息")


class BatchStartStopResponse(BaseModel):
    """批量启停响应"""

    success: list[BatchOperationItem] = Field(default_factory=list, description="成功列表")
    failed: list[BatchOperationFailedItem] = Field(default_factory=list, description="失败列表")
