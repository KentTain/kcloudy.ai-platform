"""
部门模型
"""

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from iam.models import BaseModel
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.tree import TreeNodeMixin
from iam.models.enums import DepartmentStatus


class Department(BaseModel, TreeNodeMixin, TenantMixin):
    """部门模型"""

    __tablename__ = "departments"

    # 覆盖 TreeNodeMixin 的 parent_id
    # 注意：不添加外键约束，因为顶级节点的 parent_id 为虚拟根节点 "root"（不存在于数据库）
    # 树结构的父子关系通过 parent_ids 字段维护，应用层保证一致性
    parent_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, comment="父部门ID"
    )

    # 继承 TenantMixin 的 tenant_id，不添加外键约束
    # 跨模块外键在数据库层通过迁移脚本创建，ORM 层不定义以避免 MetaData 解析问题

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

    @classmethod
    def tree_name_field(cls) -> str:
        """返回名称字段"""
        return "name"


class UserDepartment(BaseModel, TenantMixin):
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
        Index("ix_user_departments_tenant_id", "tenant_id"),
        Index("ix_user_departments_user_id", "user_id"),
        Index("ix_user_departments_department_id", "department_id"),
    )