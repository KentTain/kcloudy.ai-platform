"""
插件定义模型

对应 tenant schema 下的 plugin_definitions 表，
作为全局插件注册表，实现"有什么"（资源定义）的职责。

架构变更（2026-06-25）：
- 替代原 ai.plugins + ai.plugin_declarations 表
- declaration 字段合并了原有的 remote_declaration
- 引用计数机制（refers 字段）
"""

from sqlalchemy import Boolean, Integer, String
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from tenant.models import BaseModel
from tenant.models.enums import PluginInstallType
from framework.database.types.enum import EnumType


class TenantPluginDefinition(BaseModel, AuditMixin, ActiveRecordMixin):
    """插件定义模型

    对应 tenant schema 下的 plugin_definitions 表，
    作为全局插件注册表，实现"有什么"（资源定义）的职责。

    架构变更（2026-06-25）：
    - 替代原 ai.plugins + ai.plugin_declarations 表
    - declaration 字段合并了原有的 remote_declaration
    - 引用计数机制（refers 字段）
    """

    __tablename__ = "plugin_definitions"

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
        JSONB,
        nullable=False,
        comment="完整声明内容（manifest + 工具/模型声明）。"
                "local类型从插件包解析，remote类型从远程获取。"
                "包含：configuration、tools_configuration、"
                "models_configuration、agent_strategies_configuration",
    )
    refers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="引用计数，计算不同租户的引用计数",
    )
    install_type: Mapped[str] = mapped_column(
        EnumType(enum_class=PluginInstallType, length=16),
        nullable=False,
        index=True,
        comment="安装类型，local, remote",
    )
    manifest_type: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="清单类型",
    )
    is_recommended: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("false"),
        comment="是否推荐",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("true"),
        comment="是否启用",
    )
    # 远程插件市场相关字段
    marketplace_id: Mapped[str | None] = mapped_column(
        String(36),
        comment="来源市场ID，本地注册的为 NULL",
    )
    remote_plugin_id: Mapped[str | None] = mapped_column(
        String(128),
        comment="远程市场的插件标识",
    )
    remote_version: Mapped[str | None] = mapped_column(
        String(32),
        comment="远程最新版本",
    )
    local_version: Mapped[str | None] = mapped_column(
        String(32),
        comment="本地存储版本",
    )
    update_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("false"),
        comment="是否有新版本",
    )
    package_id: Mapped[str | None] = mapped_column(
        String(36),
        comment="关联的插件包记录",
    )
    source_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="local",
        server_default=sa.text("'local'"),
        comment="来源类型：local, remote",
    )

    __table_args__ = ({"comment": "插件定义表"},)
