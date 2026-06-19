"""
系统设置模型

定义租户级系统配置容器。
"""

from typing import TYPE_CHECKING

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from framework.database import PropertyMixin, TenantMixin
from framework.database.mixins.active_record import ActiveRecordMixin
from iam.models import BaseModel

if TYPE_CHECKING:
    from iam.models.system_setting_attribute import SystemSettingAttribute


class SystemSetting(BaseModel, TenantMixin, PropertyMixin, ActiveRecordMixin):
    """
    系统设置模型

    继承字段：
    - BaseModel: id, created_at, updated_at
    - TenantMixin: tenant_id
    - PropertyMixin: name, display_name, description, can_edit, is_require, index
    - ActiveRecordMixin: CRUD 方法

    独有字段：
    - code: 设置编号
    - application_id: 应用程序Id
    - application_name: 应用程序名称
    """

    __tablename__ = "system_settings"

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="设置编号"
    )

    application_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="应用程序Id"
    )

    application_name: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="应用程序名称"
    )

    attributes: Mapped[list["SystemSettingAttribute"]] = relationship(
        "SystemSettingAttribute",
        back_populates="setting",
        lazy="selectin",
        order_by="SystemSettingAttribute.index",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("uq_system_settings_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_system_settings_tenant_id", "tenant_id"),
    )
