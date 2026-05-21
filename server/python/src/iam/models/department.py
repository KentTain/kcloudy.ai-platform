"""
部门模型
"""

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models import BaseModel, TimestampMixin, UUIDPrimaryKeyMixin
from models.iam.enums import DepartmentStatus


class Department(
    BaseModel,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
):
    """部门模型"""

    __tablename__ = "departments"

    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, comment="父部门ID"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="部门名称"
    )
    code: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="部门编码"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="排序号"
    )
    leader_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="部门负责人ID"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DepartmentStatus.ACTIVE, comment="状态"
    )

    __table_args__ = (
        Index("ix_departments_tenant_id", "tenant_id"),
        Index("ix_departments_parent_id", "parent_id"),
        Index("ix_departments_leader_id", "leader_id"),
    )


class UserDepartment(
    BaseModel,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
):
    """用户-部门关联模型"""

    __tablename__ = "user_departments"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"
    )
    department_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, comment="部门ID"
    )
    is_leader: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="是否部门负责人"
    )

    __table_args__ = (
        Index("ix_user_departments_user_id", "user_id"),
        Index("ix_user_departments_department_id", "department_id"),
    )
