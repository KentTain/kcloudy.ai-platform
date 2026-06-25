"""
插件定义模型

对应 tenant schema 下的 plugin_definitions 表，
作为全局插件注册表，实现"有什么"（资源定义）的职责。

架构变更（2026-06-25）：
- 替代原 ai.plugins + ai.plugin_declarations 表
- declaration 字段合并了原有的 remote_declaration
- 引用计数机制（refers 字段）
"""

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from tenant.models import BaseModel


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
        String(16),
        nullable=False,
        index=True,
        comment="安装类型，local, remote",
    )
    manifest_type: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="清单类型",
    )
