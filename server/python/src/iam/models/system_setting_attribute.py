"""
系统设置属性值模型

定义系统设置的具体属性值。
"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from framework.database import BaseModel, PropertyAttributeMixin, TenantMixin

if TYPE_CHECKING:
    from iam.models.system_setting import SystemSetting


class SystemSettingAttribute(BaseModel, TenantMixin, PropertyAttributeMixin):
    """
    系统设置属性值模型

    继承字段：
    - BaseModel: id, created_at, updated_at
    - TenantMixin: tenant_id
    - PropertyAttributeMixin: data_type, name, display_name, description, value, ext_data, can_edit, is_require, index

    独有字段：
    - setting_id: 配置Id（外键）
    """

    __tablename__ = "system_setting_attributes"

    setting_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("system_settings.id", ondelete="CASCADE"),
        nullable=False,
        comment="配置Id"
    )

    setting: Mapped["SystemSetting"] = relationship(
        "SystemSetting",
        back_populates="attributes"
    )

    __table_args__ = (
        Index("uq_system_setting_attributes_setting_name", "setting_id", "name", unique=True),
        Index("ix_system_setting_attributes_setting_id", "setting_id"),
        Index("ix_system_setting_attributes_tenant_id", "tenant_id"),
    )
