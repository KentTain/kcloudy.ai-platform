"""
插件相关数据库模型

包含插件安装任务、插件凭证等模型。

架构变更（2026-06-25）：
- Plugin、PluginDeclaration、PluginInstallation 模型已迁移至 Tenant 模块
- 保留 PluginInstallTask（插件安装任务）
- 保留 PluginCredential（插件凭证）
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from ai.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin

# ======================= 枚举定义 =======================


class PluginType(str, Enum):
    """插件类型枚举

    顶层插件分类。oauth/endpoint 不是类型，而是插件包清单内声明的
    提供者能力，故不在此枚举。
    """

    MODEL = "model"  # AI模型插件（LLM、Embedding等）
    TOOL = "tool"  # 工具插件
    AGENT = "agent"  # AI代理插件
    MCP = "mcp"  # MCP 服务插件（独立的 MCP server 资源）
    SKILL = "skill"  # 技能插件（知识文档 + 简单脚本）


class InstallType(str, Enum):
    """安装类型枚举"""

    LOCAL = "local"
    REMOTE = "remote"


class RuntimeType(str, Enum):
    """运行时类型枚举"""

    LOCAL = "local"
    REMOTE = "remote"
    CONTAINER = "container"


class SourceType(str, Enum):
    """来源类型枚举"""

    PACKAGE = "package"
    MARKETPLACE = "marketplace"


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class PluginStatus(str, Enum):
    """插件运行状态枚举"""

    ACTIVE = "active"  # 活跃状态
    INACTIVE = "inactive"  # 非活跃状态


class CredentialScope(str, Enum):
    """凭证作用域

    当前阶段用于区分：
    - global: 全局
    - personal: 个人（预留，当前未使用）
    """

    GLOBAL = "global"
    PERSONAL = "personal"


# ======================= 自定义类型 =======================


class PluginConfigJSON(TypeDecorator):
    """
    PluginConfig 的自定义 JSON 序列化器
    用于处理插件配置的序列化和反序列化
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> Any:
        """将 PluginConfig 对象序列化为 JSON 格式"""
        if value is None:
            return None

        return self._custom_encoder(value)

    def process_result_value(self, value: Any, dialect) -> dict | None:
        """将 JSON 格式反序列化为字典"""
        if value is None:
            return None

        # 直接返回字典，不转换为特定对象
        if isinstance(value, dict):
            return value

        return value

    def _custom_encoder(self, obj: Any) -> Any:
        """自定义编码器，处理 Pydantic 模型序列化"""
        # 处理 Pydantic 模型
        if hasattr(obj, "model_dump"):
            return obj.model_dump(mode="json")

        # 处理列表和其他可迭代对象，递归处理其中的元素
        if isinstance(obj, list):
            return [self._custom_encoder(item) for item in obj]

        # 处理集合
        if isinstance(obj, set):
            return [self._custom_encoder(item) for item in obj]

        # 处理字典，递归处理键值
        if isinstance(obj, dict):
            return {k: self._custom_encoder(v) for k, v in obj.items()}

        # 处理 datetime
        if isinstance(obj, datetime):
            return obj.isoformat()

        # 基本类型直接返回
        return obj


# ======================= 模型定义 =======================


class PluginInstallTask(
    BaseModel,
    AuditMixin,
    ActiveRecordMixin,
    TenantMixin,
):
    """插件安装任务模型

    用于异步安装任务追踪，支持 Redis Stream 任务队列。

    状态流转：
    pending → running → completed / failed / timeout
    """

    __tablename__ = "plugin_install_tasks"

    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID",
    )
    plugin_unique_identifier: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="插件唯一标识符",
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="pending",
        comment="状态: pending, running, completed, failed, timeout",
    )
    progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="进度百分比 (0-100)",
    )
    current_step: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="当前步骤描述",
    )
    steps: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="步骤列表与状态",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始时间",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间",
    )


class PluginCredential(
    BaseModel,
    AuditMixin,
    ActiveRecordMixin,
    TenantMixin,
):
    """插件凭证（全局多凭证池，预留个人维度）

    支持为每个插件维护多个凭证，通过 is_default 字段标识默认凭证。
    节点选择凭证时，优先使用显式指定的 credential_id，否则使用默认凭证。
    """

    __tablename__ = "plugin_credentials"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_plugin_credentials_tenant_name"),
    )

    # 关联信息
    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID，manifest中的author+name，例如alon/tongyi",
    )
    # 插件类型（tool/model/agent等）
    plugin_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="插件类型",
    )

    # 作用域（当前仅使用global，personal为后续扩展预留）
    scope: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=CredentialScope.GLOBAL.value,
        comment="作用域，global全局、personal个人",
    )

    # 凭证名称（租户级唯一）
    name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="凭证名称，租户级唯一",
    )

    # 凭证内容（加密存储）
    credentials: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="凭证内容，JSON格式",
    )

    # 是否禁用
    is_disabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否禁用",
    )

    # 是否为默认凭证
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="是否为默认凭证",
    )
