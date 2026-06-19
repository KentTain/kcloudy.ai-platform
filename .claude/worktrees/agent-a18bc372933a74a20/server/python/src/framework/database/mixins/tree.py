"""
树节点混入

提供完整的树结构字段和 CRUD 方法。
"""

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar, Self

from sqlalchemy import Boolean, Integer, String, and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from framework.core.constants import (
    DEFAULT_SORT,
    DEFAULT_TREE_ROOT_ID,
    TREE_SORTS_LENGTH,
    TREE_SORTS_PADSTR,
)


class TreeNodeEventType(str, Enum):
    """树节点事件类型"""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class TreeNodeMixin:
    """
    树节点混入类

    提供完整的树结构字段和 CRUD 方法。

    字段:
    - parent_id: 父节点ID
    - tree_leaf: 是否为叶子节点
    - tree_level: 树层级
    - tree_sort: 排序号
    - tree_sorts: 排序路径
    - tree_names: 名称路径
    - parent_ids: 父ID路径
    """

    __abstract__ = True

    # ==================== 字段名常量 ====================

    __parent_id_name__: ClassVar[str] = "parent_id"
    __tree_leaf_name__: ClassVar[str] = "tree_leaf"
    __tree_level_name__: ClassVar[str] = "tree_level"
    __tree_sort_name__: ClassVar[str] = "tree_sort"
    __tree_sorts_name__: ClassVar[str] = "tree_sorts"
    __tree_names_name__: ClassVar[str] = "tree_names"
    __parent_ids_name__: ClassVar[str] = "parent_ids"
    __tree_name_separator__: ClassVar[str] = "/"

    # ==================== 字段定义 ====================

    parent_id: Mapped[str] = mapped_column(
        __parent_id_name__,
        String(36),
        nullable=False,
        default=DEFAULT_TREE_ROOT_ID,
        index=True,
        comment="父节点ID",
    )

    tree_leaf: Mapped[bool] = mapped_column(
        __tree_leaf_name__,
        Boolean,
        nullable=False,
        default=True,
        comment="是否为叶子节点",
    )

    tree_level: Mapped[int] = mapped_column(
        __tree_level_name__,
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="树层级",
    )

    tree_sort: Mapped[int] = mapped_column(
        __tree_sort_name__,
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="排序号",
    )

    tree_sorts: Mapped[str] = mapped_column(
        __tree_sorts_name__,
        String(512),
        nullable=False,
        default="",
        comment="排序路径",
    )

    tree_names: Mapped[str] = mapped_column(
        __tree_names_name__,
        String(512),
        nullable=False,
        default="",
        comment="名称路径",
    )

    parent_ids: Mapped[str] = mapped_column(
        __parent_ids_name__,
        String(1024),
        nullable=False,
        default=f"{DEFAULT_TREE_ROOT_ID},",
        comment="父ID路径",
    )

    # ==================== 辅助方法 ====================

    @classmethod
    def get_root_id(cls) -> str:
        """
        获取根节点ID

        Returns:
            str: 根节点ID
        """
        return DEFAULT_TREE_ROOT_ID

    @classmethod
    def normalize_parent_id(cls, parent_id: str | None) -> str:
        """
        标准化父节点ID

        Args:
            parent_id: 父节点ID，None 或空字符串表示根节点

        Returns:
            str: 标准化后的父节点ID
        """
        if not parent_id:
            return cls.get_root_id()
        return str(parent_id)

    @classmethod
    def is_root_parent(cls, parent_id: str | None) -> bool:
        """
        判断父节点ID是否表示根节点

        Args:
            parent_id: 父节点ID

        Returns:
            bool: 是否为根节点父ID
        """
        return cls.normalize_parent_id(parent_id) == cls.get_root_id()

    def is_root_node(self) -> bool:
        """
        判断当前节点是否为根层节点

        Returns:
            bool: 当前节点是否挂在默认根节点下
        """
        return type(self).is_root_parent(self.parent_id)

    @classmethod
    def tree_name_field(cls) -> str:
        """返回名称字段，子类应该重写此方法"""
        return "name"

    @classmethod
    def tree_name_separator(cls) -> str:
        """
        获取树名称路径分隔符

        Returns:
            str: 名称路径分隔符
        """
        return cls.__tree_name_separator__

    def get_tree_name_value(self) -> str:
        """
        获取当前节点名称字段的值

        Returns:
            str: 当前节点名称字段值
        """
        value = getattr(self, type(self).tree_name_field(), "")
        return "" if value is None else str(value)

    def get_tree_name(self) -> str:
        """
        获取可写入名称路径的节点名称

        Returns:
            str: 已转义路径分隔符的节点名称
        """
        return type(self).normalize_tree_name(self.get_tree_name_value())

    @classmethod
    def normalize_tree_name(cls, name: object) -> str:
        """
        标准化节点名称，避免名称自身破坏 tree_names 路径

        Args:
            name: 节点名称

        Returns:
            str: 标准化后的节点名称
        """
        return str(name or "").replace(cls.tree_name_separator(), "_")

    @classmethod
    def join_tree_names(cls, parent_tree_names: str | None, tree_name: object) -> str:
        """
        拼接父节点名称路径与当前节点名称

        Args:
            parent_tree_names: 父节点名称路径
            tree_name: 当前节点名称

        Returns:
            str: 当前节点完整名称路径
        """
        current_name = cls.normalize_tree_name(tree_name)
        if not parent_tree_names:
            return current_name
        parent_tree_names = parent_tree_names.rstrip(cls.tree_name_separator())
        return f"{parent_tree_names}{cls.tree_name_separator()}{current_name}"

    @classmethod
    def calculate_tree_level(cls, parent_ids: str | None) -> int | None:
        """
        根据父节点ID路径计算树层级

        根层节点的 parent_ids 通常为 DEFAULT_TREE_ROOT_ID,，层级为 0。

        Args:
            parent_ids: 父节点ID路径

        Returns:
            int | None: 树层级；parent_ids 为 None 时返回 None
        """
        if parent_ids is None:
            return None

        ids = [parent_id for parent_id in parent_ids.split(",") if parent_id]
        if not ids:
            return 0
        return max(len(ids) - 1, 0)

    @classmethod
    def _format_sort(cls, sort: int) -> str:
        """格式化排序号"""
        tree_sort_str = str(sort or 0)
        return f"{tree_sort_str.rjust(TREE_SORTS_LENGTH, TREE_SORTS_PADSTR)},"

    @classmethod
    def build_root_parent_ids(cls) -> str:
        """
        构建根层节点的父级路径

        Returns:
            str: 根层节点 parent_ids
        """
        return f"{cls.get_root_id()},"

    @classmethod
    def build_child_parent_ids(cls, parent: "TreeNodeMixin") -> str:
        """
        根据父节点构建子节点的父级路径

        Args:
            parent: 父节点

        Returns:
            str: 子节点 parent_ids
        """
        return f"{parent.parent_ids}{parent.id},"

    def apply_root_tree_fields(self) -> None:
        """按根层节点规则填充当前节点树字段"""
        self.parent_id = type(self).get_root_id()
        self.tree_level = 0
        self.tree_leaf = True
        self.parent_ids = type(self).build_root_parent_ids()
        self.tree_sorts = type(self)._format_sort(self.tree_sort)
        self.tree_names = self.get_tree_name()

    def apply_child_tree_fields(self, parent: "TreeNodeMixin") -> None:
        """
        按子节点规则填充当前节点树字段

        Args:
            parent: 父节点
        """
        self.parent_id = str(parent.id)
        self.tree_level = parent.tree_level + 1
        self.tree_leaf = True
        self.parent_ids = type(self).build_child_parent_ids(parent)
        self.tree_sorts = f"{parent.tree_sorts}{type(self)._format_sort(self.tree_sort)}"
        self.tree_names = type(self).join_tree_names(parent.tree_names, self.get_tree_name())

    def descendant_parent_ids_prefix(self) -> str:
        """
        获取后代节点 parent_ids 查询前缀

        Returns:
            str: 可用于 parent_ids LIKE \'<prefix>%\' 的前缀
        """
        return f"{self.parent_ids}{self.id},"

    # ==================== 内部方法 ====================

    @classmethod
    def _node_source_to_dict(
        cls,
        source: dict | Any,
        update_data: dict | None = None,
        exclude_unset: bool = False,
    ) -> dict[str, Any]:
        """将字典、Pydantic 对象或普通对象转换为树节点数据。"""
        if isinstance(source, dict):
            data = source.copy()
        elif hasattr(source, "model_dump"):
            data = source.model_dump(exclude_unset=exclude_unset)
        else:
            data = {}
            for column in cls.__table__.columns:
                if hasattr(source, column.name):
                    data[column.name] = getattr(source, column.name)

        if update_data:
            data.update(update_data)

        return data

    @classmethod
    def _node_primary_key_column(cls):
        pk_columns = cls.__table__.primary_key
        if not pk_columns:
            raise AttributeError("模型没有主键")
        return next(iter(pk_columns))

    @classmethod
    def _node_primary_key_value(cls, obj: "TreeNodeMixin") -> Any:
        pk_column = cls._node_primary_key_column()
        return getattr(obj, pk_column.name)

    @classmethod
    def _node_not_deleted_condition(cls):
        """检查模型是否支持软删除"""
        if hasattr(cls, "deleted_at"):
            return getattr(cls, "deleted_at").is_(None)
        return None

    @classmethod
    def _node_conditions(
        cls,
        extra_conditions: list | None = None,
        include_deleted: bool = False,
    ) -> list:
        """构建查询条件"""
        conditions = list(extra_conditions or [])
        if not include_deleted:
            not_deleted_condition = cls._node_not_deleted_condition()
            if not_deleted_condition is not None:
                conditions.append(not_deleted_condition)
        return conditions

    @classmethod
    async def _publish_node_event(
        cls,
        event_type: TreeNodeEventType,
        data: Any,
    ) -> None:
        """
        发布树节点事件

        业务模块可通过定义 _publish_event 方法启用事件发布。

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        publisher = getattr(cls, "_publish_event", None)
        if publisher:
            await publisher(event_type, data)

    @classmethod
    async def _get_next_sort(
        cls,
        session: AsyncSession,
        parent_id: str,
        extra_conditions: list | None = None,
    ) -> int:
        """获取下一个排序号"""
        conditions = [
            cls.parent_id == parent_id,
            *cls._node_conditions(extra_conditions),
        ]
        result = await session.execute(
            select(func.max(cls.tree_sort)).where(and_(*conditions))
        )
        max_sort = result.scalar()
        return (max_sort or 0) + DEFAULT_SORT

    @classmethod
    async def _refresh_parent_leaf_status(
        cls,
        session: AsyncSession,
        parent_id: str,
        extra_conditions: list | None = None,
    ) -> None:
        """刷新父节点的叶子状态"""
        parent_id = cls.normalize_parent_id(parent_id)
        if cls.is_root_parent(parent_id):
            return

        conditions = [
            cls.parent_id == parent_id,
            *cls._node_conditions(extra_conditions),
        ]
        result = await session.execute(
            select(func.count()).select_from(cls).where(and_(*conditions))
        )
        child_count = result.scalar() or 0

        # 获取父节点
        node = await cls.one_node(session, parent_id, extra_conditions)
        if node:
            node.tree_leaf = child_count == 0

    @classmethod
    async def one_node(
        cls,
        session: AsyncSession,
        id: Any,
        extra_conditions: list | None = None,
        include_deleted: bool = False,
    ) -> Self | None:
        """
        根据主键获取未删除树节点。

        Args:
            session: 数据库会话
            id: 节点主键
            extra_conditions: 额外业务边界，例如 tenant_id/workspace_id
            include_deleted: 是否包含软删除节点
        """
        pk_column = cls._node_primary_key_column()
        conditions = [
            getattr(cls, pk_column.name) == id,
            *cls._node_conditions(extra_conditions, include_deleted),
        ]
        result = await session.execute(select(cls).where(and_(*conditions)))
        return result.scalar_one_or_none()

    @classmethod
    async def _node_parent(
        cls,
        session: AsyncSession,
        parent_id: str | None,
        extra_conditions: list | None = None,
    ) -> Self | None:
        """获取父节点"""
        parent_id = cls.normalize_parent_id(parent_id)
        if cls.is_root_parent(parent_id):
            return None

        parent = await cls.one_node(session, parent_id, extra_conditions)
        if parent is None:
            raise ValueError(f"父节点 {parent_id} 不存在")
        return parent

    # ==================== CRUD 方法 ====================

    @classmethod
    async def create_node(
        cls,
        session: AsyncSession,
        source: dict | Any,
        update_data: dict | None = None,
        extra_conditions: list | None = None,
    ) -> Self:
        """
        创建树节点，并自动维护 tree_* 与 parent_ids 字段。

        事务由调用方控制；本方法只执行 flush。

        Args:
            session: 数据库会话
            source: 节点属性字典
            update_data: 额外更新数据
            extra_conditions: 额外业务边界条件

        Returns:
            创建的节点
        """
        data = cls._node_source_to_dict(source, update_data)
        parent_id = cls.normalize_parent_id(data.get("parent_id"))
        data["parent_id"] = parent_id

        if not data.get("tree_sort"):
            data["tree_sort"] = await cls._get_next_sort(
                session, parent_id, extra_conditions
            )

        obj = cls()
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

        parent = await cls._node_parent(session, parent_id, extra_conditions)
        if parent is None:
            obj.apply_root_tree_fields()
        else:
            obj.apply_child_tree_fields(parent)
            parent.tree_leaf = False

        session.add(obj)
        await session.flush()
        await cls._publish_node_event(TreeNodeEventType.CREATED, obj)
        return obj

    @classmethod
    async def update_node(
        cls,
        session: AsyncSession,
        id: Any,
        source: dict | Any,
        update_data: dict | None = None,
        extra_conditions: list | None = None,
    ) -> Self:
        """
        更新树节点，并在名称、排序或父节点变化时级联刷新子孙节点路径。

        事务由调用方控制；本方法只执行 flush。

        Args:
            session: 数据库会话
            id: 节点ID
            source: 更新属性字典
            update_data: 额外更新数据
            extra_conditions: 额外业务边界条件

        Returns:
            更新后的节点
        """
        node = await cls.one_node(session, id, extra_conditions)
        if node is None:
            raise ValueError(f"节点不存在: {id}")

        pk_value = cls._node_primary_key_value(node)
        old_parent_id = node.parent_id
        old_parent_ids = node.parent_ids
        old_tree_sorts = node.tree_sorts
        old_tree_names = node.tree_names
        old_tree_level = node.tree_level
        old_tree_leaf = node.tree_leaf
        old_descendant_prefix = node.descendant_parent_ids_prefix()

        data = cls._node_source_to_dict(source, update_data, exclude_unset=True)
        data.pop(cls._node_primary_key_column().name, None)
        data.pop("tree_leaf", None)
        new_parent_id = cls.normalize_parent_id(data.get("parent_id", old_parent_id))

        if str(new_parent_id) == str(pk_value):
            raise ValueError("父节点不能设置为当前节点")

        for key, value in data.items():
            if hasattr(node, key):
                setattr(node, key, value)

        node.parent_id = new_parent_id
        parent = await cls._node_parent(session, new_parent_id, extra_conditions)

        if parent is not None:
            parent_pk_value = cls._node_primary_key_value(parent)
            if str(parent_pk_value) == str(pk_value):
                raise ValueError("父节点不能设置为当前节点")
            if parent.parent_ids.startswith(old_descendant_prefix):
                raise ValueError("父节点不能设置为当前节点的子孙节点")

        if not node.tree_sort:
            node.tree_sort = await cls._get_next_sort(
                session, new_parent_id, extra_conditions
            )

        if parent is None:
            node.apply_root_tree_fields()
        else:
            node.apply_child_tree_fields(parent)
            parent.tree_leaf = False

        node.tree_leaf = old_tree_leaf
        new_descendant_prefix = node.descendant_parent_ids_prefix()
        level_delta = node.tree_level - old_tree_level

        path_changed = (
            old_parent_ids != node.parent_ids
            or old_tree_sorts != node.tree_sorts
            or old_tree_names != node.tree_names
        )
        if path_changed:
            conditions = [
                cls.parent_ids.like(f"{old_descendant_prefix}%"),
                *cls._node_conditions(extra_conditions),
            ]
            await session.execute(
                update(cls)
                .where(and_(*conditions))
                .values(
                    parent_ids=func.replace(
                        cls.parent_ids,
                        old_descendant_prefix,
                        new_descendant_prefix,
                    ),
                    tree_sorts=func.replace(
                        cls.tree_sorts,
                        old_tree_sorts,
                        node.tree_sorts,
                    ),
                    tree_names=func.replace(
                        cls.tree_names,
                        old_tree_names,
                        node.tree_names,
                    ),
                    tree_level=cls.tree_level + level_delta,
                )
            )

        if old_parent_id != new_parent_id:
            await cls._refresh_parent_leaf_status(
                session, old_parent_id, extra_conditions
            )

        await session.flush()
        await cls._publish_node_event(TreeNodeEventType.UPDATED, node)
        return node

    @classmethod
    async def delete_node(
        cls,
        session: AsyncSession,
        id: Any,
        extra_conditions: list | None = None,
    ) -> int:
        """
        删除树节点及全部子孙节点。

        如果模型有 deleted_at 字段则执行软删除，否则执行物理删除。

        Args:
            session: 数据库会话
            id: 节点ID
            extra_conditions: 额外业务边界条件

        Returns:
            删除的节点数量
        """
        node = await cls.one_node(session, id, extra_conditions)
        if node is None:
            return 0

        old_parent_id = node.parent_id
        descendant_prefix = node.descendant_parent_ids_prefix()
        descendant_conditions = [
            cls.parent_ids.like(f"{descendant_prefix}%"),
            *cls._node_conditions(extra_conditions),
        ]

        affected_rows = 1
        if hasattr(cls, "deleted_at"):
            # 软删除
            now = datetime.now(UTC).replace(tzinfo=None)
            result = await session.execute(
                update(cls).where(and_(*descendant_conditions)).values(deleted_at=now)
            )
            affected_rows += result.rowcount or 0

            node.deleted_at = now
            await session.flush()
        else:
            # 物理删除
            result = await session.execute(
                select(cls)
                .where(and_(*descendant_conditions))
                .order_by(cls.tree_level.desc())
            )
            descendants = list(result.scalars().all())
            affected_rows += len(descendants)
            for descendant in descendants:
                await session.delete(descendant)
            await session.delete(node)
            await session.flush()

        await cls._refresh_parent_leaf_status(session, old_parent_id, extra_conditions)
        await session.flush()
        await cls._publish_node_event(TreeNodeEventType.DELETED, {"id": id, "count": affected_rows})
        return affected_rows

    @classmethod
    async def list_nodes(
        cls,
        session: AsyncSession,
        extra_conditions: list | None = None,
        fuzzy_fields: dict[str, str] | None = None,
        include_deleted: bool = False,
    ) -> Sequence[Self]:
        """
        按 tree_sorts 获取树节点平铺列表。

        Args:
            session: 数据库会话
            extra_conditions: 额外业务边界条件
            fuzzy_fields: 模糊查询字段
            include_deleted: 是否包含软删除节点

        Returns:
            按 tree_sorts 排序的节点列表
        """
        conditions = cls._node_conditions(extra_conditions, include_deleted)
        if fuzzy_fields:
            for field, value in fuzzy_fields.items():
                if value and hasattr(cls, field):
                    conditions.append(getattr(cls, field).like(f"%{value}%"))

        statement = select(cls).order_by(cls.tree_sorts)
        if conditions:
            statement = statement.where(and_(*conditions))

        result = await session.execute(statement)
        return result.scalars().all()

    @classmethod
    def build_tree(
        cls,
        nodes: Sequence[Any],
        parent_id: str | None = None,
        transform_func: Callable[[Any], Any] | None = None,
    ) -> list[Any]:
        """
        将平铺树节点列表组装成 children 树。

        Args:
            nodes: 平铺节点列表
            parent_id: 指定父节点ID，构建子树
            transform_func: 节点转换函数

        Returns:
            树形结构列表
        """
        normalized_parent_id = cls.normalize_parent_id(parent_id)
        tree = []
        for node in nodes:
            if isinstance(node, dict):
                node_parent_id = cls.normalize_parent_id(node.get("parent_id"))
                node_id = str(node.get("id", ""))
            else:
                node_parent_id = cls.normalize_parent_id(node.parent_id)
                node_id = str(node.id)

            if node_parent_id != normalized_parent_id:
                continue

            children = cls.build_tree(nodes, node_id, transform_func)
            target_node = transform_func(node) if transform_func else node
            if isinstance(target_node, dict):
                target_node["children"] = children
            else:
                target_node.children = children
            tree.append(target_node)
        return tree


# 向后兼容别名
TreeMixin = TreeNodeMixin