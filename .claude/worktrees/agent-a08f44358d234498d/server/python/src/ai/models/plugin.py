"""
插件相关数据库模型

包含插件、插件安装、插件凭证等模型。
"""

from datetime import datetime
from typing import Any
from enum import Enum

from loguru import logger
from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from ai.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin


# ======================= 枚举定义 =======================


class PluginType(str, Enum):
    """插件类型枚举"""

    MODEL = "model"  # AI模型插件（LLM、Embedding等）
    TOOL = "tool"  # 工具插件
    AGENT = "agent"  # AI代理插件
    OAUTH = "oauth"  # OAuth认证插件
    ENDPOINT = "endpoint"  # 端点插件


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

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


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


class Plugin(BaseModel, AuditMixin, ActiveRecordMixin):
    """插件模型，全局，不分租户"""

    __tablename__ = "plugins"

    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID，manifest中的author+name，例如alon/tongyi",
    )
    plugin_unique_identifier: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        unique=True,
        comment="插件唯一标识符，格式：{plugin_id}:{version}@{校验和}",
    )
    # 引用计数
    refers: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="引用计数，计算不同租户的引用计数"
    )
    # 安装类型
    install_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        index=True,
        comment="安装类型，local, remote",
    )
    # 清单类型
    manifest_type: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="清单类型"
    )
    remote_declaration: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="远程声明，当插件为远程类型时启用",
    )


class PluginDeclaration(BaseModel, AuditMixin, ActiveRecordMixin):
    """插件声明模型，全局，不分租户"""

    __tablename__ = "plugin_declarations"

    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID，manifest中的author+name，例如alon/tongyi",
    )
    plugin_unique_identifier: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        unique=True,
        comment="插件唯一标识符，格式：{plugin_id}:{version}@{校验和}",
    )
    declaration: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="声明内容，插件完整声明内容，包括插件的manifest信息+里面的工具、模型等信息",
    )


class PluginInstallation(
    BaseModel,
    AuditMixin,
    ActiveRecordMixin,
    TenantMixin,
):
    """插件安装记录，按租户隔离"""

    __tablename__ = "plugin_installations"

    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID，manifest中的author+name，例如alon/tongyi",
    )
    plugin_unique_identifier: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        index=True,
        comment="插件唯一标识符，格式：{plugin_id}:{version}@{校验和}",
    )
    runtime_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="运行时类型，local, remote, container",
    )
    plugin_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="插件类型，tool, model, agent, etc.",
    )

    # === 运行状态管理字段 ===
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=PluginStatus.ACTIVE.value,
        comment="插件运行状态",
    )

    # === 生命周期时间戳 ===
    installed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="安装完成时间"
    )
    last_started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最后启动时间"
    )
    last_stopped_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最后停止时间"
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后访问时间（用于冻结判断）",
    )
    frozen_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="冻结时间"
    )

    # === 运行时信息 ===
    process_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="进程ID（运行时）"
    )
    port: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="运行端口（运行时）"
    )
    work_directory: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="工作目录路径"
    )

    # === 性能和健康状态 ===
    call_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="调用次数统计"
    )
    error_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="错误次数统计"
    )
    last_error: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="最后错误信息"
    )
    health_check_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最后健康检查时间"
    )

    # === 安装配置信息 ===
    install_config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="安装时的配置信息（依赖版本、环境信息等）",
    )
    runtime_config: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="运行时配置信息"
    )

    # === 自动管理配置 ===
    auto_start: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="服务重启时是否自动启动"
    )
    freeze_threshold_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=24,
        comment="冻结阈值（小时），超过此时间未访问则自动冻结",
    )

    endpoints_setups: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="端点设置数"
    )
    endpoints_active: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="活跃端点数"
    )
    source: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="来源，package, marketplace",
    )
    meta: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="元数据, json格式，marketplace会记录插件的meta信息",
    )
    plugin_config: Mapped[dict | None] = mapped_column(
        PluginConfigJSON,
        nullable=True,
        comment="插件配置, json格式，marketplace会记录插件的配置信息",
    )


class PluginInstallTask(
    BaseModel,
    AuditMixin,
    ActiveRecordMixin,
    TenantMixin,
):
    """插件安装任务模型"""

    __tablename__ = "plugin_install_tasks"

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="状态，running, success, failed",
    )
    total_plugins: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="总插件数"
    )
    completed_plugins: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="已完成插件数"
    )
    plugins: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="插件状态列表，json格式，包含插件ID、状态、错误信息等",
    )


class PluginCredential(
    BaseModel,
    AuditMixin,
    ActiveRecordMixin,
    TenantMixin,
):
    """插件凭证（全局多凭证池，预留个人维度）

    注意：默认全局凭证仍存放在 PluginInstallation.runtime_config.credentials 中，本表不维护默认。
    节点选择扩展凭证时需要显式指定 credential_id。
    """

    __tablename__ = "plugin_credentials"

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
        comment="凭证作用域：global(全局)/personal(个人)",
    )

    # 基本信息
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="凭证名称")
    provider_name: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="工具提供者名"
    )

    # 凭证内容（密文字段加密在服务层处理，这里按JSON存储）
    credentials: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="凭证JSON（密文字段加密）"
    )
