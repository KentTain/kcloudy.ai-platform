"""插件市场 API Schema"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from framework.schemas import BaseModel, BasePaginatedQuery
from pydantic import Field


# ==================== 请求 Schema ====================


class MarketplaceCreate(BaseModel):
    """创建市场请求"""

    name: str = Field(..., min_length=1, max_length=100, description="市场名称")
    code: str = Field(..., min_length=1, max_length=50, description="市场编码")
    type: str = Field(..., min_length=1, max_length=50, description="市场类型")
    url: str = Field(..., min_length=1, max_length=500, description="市场地址")
    auth_type: str = Field(default="none", max_length=50, description="认证类型")
    auth_config: dict | None = Field(default=None, description="认证配置")
    description: str | None = Field(default=None, max_length=500, description="市场描述")


class MarketplaceUpdate(BaseModel):
    """更新市场请求"""

    name: str | None = Field(default=None, min_length=1, max_length=100, description="市场名称")
    url: str | None = Field(default=None, min_length=1, max_length=500, description="市场地址")
    auth_type: str | None = Field(default=None, max_length=50, description="认证类型")
    auth_config: dict | None = Field(default=None, description="认证配置")
    is_enabled: bool | None = Field(default=None, description="是否启用")
    sync_config: dict | None = Field(default=None, description="同步配置")
    description: str | None = Field(default=None, max_length=500, description="市场描述")


class SyncPluginItem(BaseModel):
    """单个同步插件项"""
    plugin_id: str = Field(..., description="插件ID")
    plugin_type: str = Field(default="tool", description="插件类型")


class SyncPluginsRequest(BaseModel):
    """同步插件请求"""

    marketplace_id: str = Field(..., description="市场ID")
    plugins: list[SyncPluginItem] = Field(..., description="同步插件列表")


# ==================== 响应 Schema ====================


class MarketplaceResponse(BaseModel):
    """市场响应"""

    id: str = Field(..., description="市场ID")
    name: str = Field(..., description="市场名称")
    code: str = Field(..., description="市场编码")
    type: str = Field(..., description="市场类型")
    url: str = Field(..., description="市场地址")
    auth_type: str = Field(..., description="认证类型")
    is_enabled: bool = Field(..., description="是否启用")
    last_sync_at: datetime | None = Field(default=None, description="最后同步时间")
    last_sync_status: str | None = Field(default=None, description="最后同步状态")
    description: str | None = Field(default=None, description="市场描述")
    supported_types: list[str] = Field(default_factory=list, description="市场支持的插件类型")
    created_at: datetime | None = Field(default=None, description="创建时间")
    updated_at: datetime | None = Field(default=None, description="更新时间")

    SKILL_MARKET_TYPES: ClassVar[set[str]] = {"agentskills", "modelscope-skill", "local-skill"}

    @classmethod
    def from_entity(cls, entity) -> MarketplaceResponse:
        """从实体转换"""
        supported_types = (
            ["skill"] if entity.type in cls.SKILL_MARKET_TYPES
            else ["tool", "model", "agent", "extension"]
        )
        return cls(
            id=entity.id,
            name=entity.name,
            code=entity.code,
            type=entity.type,
            url=entity.url,
            auth_type=entity.auth_type,
            is_enabled=entity.is_enabled,
            last_sync_at=entity.last_sync_at,
            last_sync_status=entity.last_sync_status,
            description=entity.description,
            supported_types=supported_types,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class MarketplaceTestResponse(BaseModel):
    """市场测试响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    plugin_count: int | None = Field(default=None, description="插件数量")
    latency_ms: int | None = Field(default=None, description="延迟毫秒数")


class RemotePluginResponse(BaseModel):
    """远程插件响应"""

    plugin_id: str = Field(..., description="插件ID")
    name: str = Field(..., description="插件名称")
    description: str | None = Field(default=None, description="插件描述")
    version: str = Field(..., description="插件版本")
    author: str = Field(..., description="作者")
    icon: str | None = Field(default=None, description="图标")
    plugin_type: str = Field(..., description="插件类型")
    skill_type: str | None = Field(default=None, description="Skill 类型：knowledge | script")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    downloads: int | None = Field(default=None, description="下载次数")
    download_url: str = Field(..., description="下载地址")

    @classmethod
    def from_info(cls, info) -> RemotePluginResponse:
        """从插件信息转换"""
        return cls(
            plugin_id=info.plugin_id,
            name=info.name,
            description=info.description,
            version=info.version,
            author=info.author,
            icon=info.icon,
            plugin_type=info.plugin_type,
            skill_type=getattr(info, "skill_type", None),
            tags=info.tags,
            downloads=info.downloads,
            download_url=info.download_url,
        )


class SyncSuccessItem(BaseModel):
    """同步成功项"""
    plugin_id: str = Field(..., description="插件ID")
    version: str = Field(..., description="版本")


class SyncFailedItem(BaseModel):
    """同步失败项"""
    plugin_id: str = Field(..., description="插件ID")
    message: str = Field(..., description="错误信息")


class SyncSkippedItem(BaseModel):
    """跳过项"""
    plugin_id: str = Field(..., description="插件ID")
    reason: str = Field(..., description="跳过原因")


class SyncResultResponse(BaseModel):
    """同步结果响应"""
    success: list[SyncSuccessItem] = Field(default_factory=list, description="成功同步的插件")
    failed: list[SyncFailedItem] = Field(default_factory=list, description="失败的插件")
    skipped: list[SyncSkippedItem] = Field(default_factory=list, description="跳过的插件")


# ==================== 更新 Schema ====================


class PluginUpdateResponse(BaseModel):
    """插件更新响应"""
    plugin_id: str = Field(..., description="插件ID")
    current_version: str = Field(..., description="当前版本")
    latest_version: str = Field(..., description="最新版本")
    has_update: bool = Field(..., description="是否有更新")


class ApplyUpdateRequest(BaseModel):
    """应用更新请求"""
    marketplace_id: str = Field(..., description="市场ID")


class ApplyUpdateResult(BaseModel):
    """应用更新结果"""
    plugin_id: str = Field(..., description="插件ID")
    old_version: str = Field(..., description="旧版本")
    new_version: str = Field(..., description="新版本")
    status: str = Field(..., description="状态")


# ==================== 插件定义响应 ====================


class PluginDefinitionResponse(BaseModel):
    """插件定义响应（简要）"""

    plugin_id: str = Field(..., description="插件ID")
    plugin_unique_identifier: str = Field(..., description="插件唯一标识符")
    manifest_type: str | None = Field(default=None, description="清单类型")
    skill_type: str | None = Field(default=None, description="Skill 类型")
    runtime_type: str | None = Field(default=None, description="运行时类型")
    source_type: str = Field(default="remote", description="来源类型")
    is_enabled: bool = Field(default=True, description="是否启用")

    @classmethod
    def from_entity(cls, entity) -> PluginDefinitionResponse:
        """从实体转换"""
        return cls(
            plugin_id=entity.plugin_id,
            plugin_unique_identifier=entity.plugin_unique_identifier,
            manifest_type=entity.manifest_type,
            skill_type=entity.skill_type,
            runtime_type=entity.runtime_type,
            source_type=entity.source_type,
            is_enabled=entity.is_enabled,
        )


# ==================== 查询 Schema ====================


class MarketplaceQuery(BasePaginatedQuery):
    """市场查询"""

    type: str | None = Field(default=None, description="市场类型")
    is_enabled: bool | None = Field(default=None, description="是否启用")
