"""
树节点混入

提供完整的树结构字段和 CRUD 方法。
"""

from enum import Enum
from typing import Any, Self, Sequence
from sqlalchemy import String, Integer, Boolean, select, or_, delete
from sqlalchemy.orm import Mapped, mapped_column

from framework.core.constants import (
    DEFAULT_SORT,
    TREE_SORTS_LENGTH,
    TREE_SORTS_PADSTR,
    DEFAULT_TREE_ROOT_ID,
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

    # ==================== 字段定义 ====================

    parent_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        default=DEFAULT_TREE_ROOT_ID,
        index=True,
        comment="父节点ID"
    )

    tree_leaf: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否为叶子节点"
    )

    tree_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="树层级"
    )

    tree_sort: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="排序号"
    )

    tree_sorts: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default="",
        comment="排序路径"
    )

    tree_names: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default="",
        comment="名称路径"
    )

    parent_ids: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default=f"{DEFAULT_TREE_ROOT_ID},",
        comment="父ID路径"
    )

    # ==================== 类方法 ====================

    @classmethod
    def tree_name_field(cls) -> str:
        """返回名称字段，子类应该重写此方法"""
        return "name"

    @classmethod
    def _format_sort(cls, sort: int) -> str:
        """格式化排序号"""
        return str(sort).zfill(TREE_SORTS_LENGTH) + ","

    @classmethod
    async def _get_next_sort(
        cls,
        session,
        parent_id: str | None = None
    ) -> int:
        """获取下一个排序号"""
        parent_id = parent_id or DEFAULT_TREE_ROOT_ID
        stmt = select(cls.tree_sort).where(cls.parent_id == parent_id).order_by(cls.tree_sort.desc()).limit(1)
        result = await session.execute(stmt)
        max_sort = result.scalar_one_or_none()
        return (max_sort or 0) + DEFAULT_SORT

    @classmethod
    async def _refresh_parent_leaf_status(
        cls,
        session,
        parent_id: str
    ) -> None:
        """刷新父节点的叶子状态"""
        if parent_id == DEFAULT_TREE_ROOT_ID:
            return

        stmt = select(cls).where(cls.id == parent_id)
        result = await session.execute(stmt)
        parent = result.scalar_one_or_none()

        if parent:
            child_stmt = select(cls).where(cls.parent_id == parent_id).limit(1)
            child_result = await session.execute(child_stmt)
            has_children = child_result.scalar_one_or_none() is not None
            parent.tree_leaf = not has_children

    @classmethod
    async def _update_descendants_tree_names(
        cls,
        session,
        node_id: str,
        new_tree_names: str
    ) -> None:
        """更新子孙节点的 tree_names"""
        stmt = select(cls).where(cls.parent_ids.contains(f"{node_id},"))
        result = await session.execute(stmt)
        descendants = result.scalars().all()

        for descendant in descendants:
            # 替换 tree_names 前缀
            old_prefix = descendant.tree_names.rsplit("/", 1)[0] if "/" in descendant.tree_names else ""
            if old_prefix:
                descendant.tree_names = descendant.tree_names.replace(old_prefix, new_tree_names, 1)

    @classmethod
    async def _is_descendant(
        cls,
        session,
        node_id: str,
        target_id: str
    ) -> bool:
        """检查 target_id 是否是 node_id 的子孙节点"""
        stmt = select(cls).where(cls.id == target_id)
        result = await session.execute(stmt)
        target = result.scalar_one_or_none()

        if not target:
            return False

        return f"{node_id}," in target.parent_ids

    @classmethod
    async def _publish_node_event(
        cls,
        event_type: TreeNodeEventType,
        data: Any
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

    # ==================== CRUD 方法 ====================

    @classmethod
    async def create_node(
        cls,
        session,
        source: dict[str, Any]
    ) -> Self:
        """
        创建树节点

        自动维护树字段：
        - tree_level, tree_sorts, tree_names, parent_ids
        - 父节点的 tree_leaf 状态

        Args:
            session: 数据库会话
            source: 节点属性字典

        Returns:
            创建的节点
        """
        parent_id = source.get("parent_id", DEFAULT_TREE_ROOT_ID)
        if not parent_id:
            parent_id = DEFAULT_TREE_ROOT_ID

        # 获取或计算排序号
        tree_sort = source.get("tree_sort")
        if tree_sort is None:
            tree_sort = await cls._get_next_sort(session, parent_id)

        # 获取名称
        name = source.get(cls.tree_name_field(), "")

        # 计算树字段
        if parent_id == DEFAULT_TREE_ROOT_ID:
            # 根节点
            tree_level = 0
            parent_ids = f"{DEFAULT_TREE_ROOT_ID},"
            tree_sorts = cls._format_sort(tree_sort)
            tree_names = name
        else:
            # 子节点：获取父节点信息
            stmt = select(cls).where(cls.id == parent_id)
            result = await session.execute(stmt)
            parent = result.scalar_one_or_none()

            if not parent:
                raise ValueError(f"父节点不存在: {parent_id}")

            tree_level = parent.tree_level + 1
            parent_ids = f"{parent.parent_ids}{parent.id},"
            tree_sorts = f"{parent.tree_sorts}{cls._format_sort(tree_sort)}"
            tree_names = f"{parent.tree_names}/{name}"

            # 更新父节点的叶子状态
            parent.tree_leaf = False

        # 创建节点
        # 从 source 中移除已处理的字段，避免重复传递
        node_data = {k: v for k, v in source.items() if k not in ["parent_id", "tree_sort", "tree_leaf", "tree_level", "tree_sorts", "tree_names", "parent_ids"]}
        instance = cls(
            **node_data,
            parent_id=parent_id,
            tree_leaf=True,
            tree_level=tree_level,
            tree_sort=tree_sort,
            tree_sorts=tree_sorts,
            tree_names=tree_names,
            parent_ids=parent_ids,
        )

        session.add(instance)
        await session.flush()

        # 发布创建事件
        await cls._publish_node_event(TreeNodeEventType.CREATED, instance.to_dict() if hasattr(instance, "to_dict") else {"id": instance.id})

        return instance

    @classmethod
    async def update_node(
        cls,
        session,
        id: str,
        source: dict[str, Any]
    ) -> Self:
        """
        更新树节点

        支持：
        - 更新名称（级联更新子孙节点的 tree_names）
        - 移动节点（级联更新子孙节点的树字段）
        - 阻止循环引用

        Args:
            session: 数据库会话
            id: 节点ID
            source: 更新属性字典

        Returns:
            更新后的节点
        """
        # 获取节点
        stmt = select(cls).where(cls.id == id)
        result = await session.execute(stmt)
        node = result.scalar_one_or_none()

        if not node:
            raise ValueError(f"节点不存在: {id}")

        old_parent_id = node.parent_id
        new_parent_id = source.get("parent_id", old_parent_id)
        name_field = cls.tree_name_field()
        new_name = source.get(name_field)

        # 检查是否需要移动
        if new_parent_id != old_parent_id:
            # 阻止循环引用
            if await cls._is_descendant(session, id, new_parent_id):
                raise ValueError("不能将节点移动到其子孙节点下")

            # 更新父节点和树字段
            if new_parent_id == DEFAULT_TREE_ROOT_ID:
                # 移动到根节点
                node.parent_id = DEFAULT_TREE_ROOT_ID
                node.tree_level = 0
                node.parent_ids = f"{DEFAULT_TREE_ROOT_ID},"
                node.tree_sorts = cls._format_sort(node.tree_sort)
                if new_name:
                    node.tree_names = new_name
                elif name_field in source:
                    pass
                else:
                    node.tree_names = getattr(node, name_field)
            else:
                # 移动到新父节点
                stmt = select(cls).where(cls.id == new_parent_id)
                result = await session.execute(stmt)
                new_parent = result.scalar_one_or_none()

                if not new_parent:
                    raise ValueError(f"父节点不存在: {new_parent_id}")

                node.parent_id = new_parent_id
                node.tree_level = new_parent.tree_level + 1
                node.parent_ids = f"{new_parent.parent_ids}{new_parent.id},"
                node.tree_sorts = f"{new_parent.tree_sorts}{cls._format_sort(node.tree_sort)}"
                node.tree_names = f"{new_parent.tree_names}/{getattr(node, name_field)}"

                # 更新新父节点的叶子状态
                new_parent.tree_leaf = False

            # 刷新原父节点的叶子状态
            if old_parent_id != DEFAULT_TREE_ROOT_ID:
                await cls._refresh_parent_leaf_status(session, old_parent_id)

            # 级联更新子孙节点
            await cls._update_descendants_tree_fields(session, id)

        # 更新名称
        elif new_name and new_name != getattr(node, name_field):
            setattr(node, name_field, new_name)
            # 更新 tree_names
            old_tree_names = node.tree_names
            if node.tree_level == 0:
                node.tree_names = new_name
            else:
                parent_prefix = old_tree_names.rsplit("/", 1)[0]
                node.tree_names = f"{parent_prefix}/{new_name}"

            # 级联更新子孙节点的 tree_names
            await cls._update_descendants_tree_names(session, id, node.tree_names)

        # 更新其他字段
        for key, value in source.items():
            if key not in ["parent_id", name_field] and hasattr(node, key):
                setattr(node, key, value)

        await session.flush()

        # 发布更新事件
        await cls._publish_node_event(TreeNodeEventType.UPDATED, node.to_dict() if hasattr(node, "to_dict") else {"id": node.id})

        return node

    @classmethod
    async def _update_descendants_tree_fields(
        cls,
        session,
        node_id: str
    ) -> None:
        """
        级联更新子孙节点的树字段

        当节点移动后，需要递归更新其所有子孙节点的：
        - tree_level
        - tree_sorts
        - tree_names
        - parent_ids
        """
        # 获取已移动的节点
        stmt = select(cls).where(cls.id == node_id)
        result = await session.execute(stmt)
        moved_node = result.scalar_one_or_none()

        if not moved_node:
            return

        # 递归更新子孙节点
        async def update_children(parent: Any) -> None:
            stmt = select(cls).where(cls.parent_id == parent.id)
            result = await session.execute(stmt)
            children = result.scalars().all()

            for child in children:
                # 更新子节点的树字段
                child.tree_level = parent.tree_level + 1
                child.parent_ids = f"{parent.parent_ids}{parent.id},"
                child.tree_sorts = f"{parent.tree_sorts}{cls._format_sort(child.tree_sort)}"
                child.tree_names = f"{parent.tree_names}/{getattr(child, cls.tree_name_field())}"

                # 递归更新孙子节点
                await update_children(child)

        await update_children(moved_node)

    @classmethod
    async def delete_node(
        cls,
        session,
        id: str
    ) -> int:
        """
        删除树节点

        - 叶子节点：直接删除（或软删除）
        - 非叶子节点：级联删除所有子孙节点
        - 支持软删除：如果模型有 deleted_at 字段，执行软删除

        Args:
            session: 数据库会话
            id: 节点ID

        Returns:
            删除的节点数量
        """
        from datetime import datetime

        # 获取节点
        stmt = select(cls).where(cls.id == id)
        result = await session.execute(stmt)
        node = result.scalar_one_or_none()

        if not node:
            return 0

        parent_id = node.parent_id
        count = 0
        supports_soft_delete = hasattr(cls, "deleted_at")

        # 检查是否有子节点
        if node.tree_leaf:
            # 叶子节点：直接删除（或软删除）
            if supports_soft_delete:
                node.deleted_at = datetime.utcnow()
            else:
                await session.delete(node)
            count = 1
        else:
            # 非叶子节点：级联删除
            # 查找所有子孙节点
            stmt = select(cls).where(cls.parent_ids.contains(f"{id},"))
            result = await session.execute(stmt)
            descendants = result.scalars().all()

            # 删除（或软删除）子孙节点
            for descendant in descendants:
                if supports_soft_delete:
                    descendant.deleted_at = datetime.utcnow()
                else:
                    await session.delete(descendant)
                count += 1

            # 删除（或软删除）自身
            if supports_soft_delete:
                node.deleted_at = datetime.utcnow()
            else:
                await session.delete(node)
            count += 1

        # 刷新父节点的叶子状态
        if parent_id != DEFAULT_TREE_ROOT_ID:
            await cls._refresh_parent_leaf_status(session, parent_id)

        await session.flush()

        # 发布删除事件
        await cls._publish_node_event(TreeNodeEventType.DELETED, {"id": id, "count": count})

        return count

    @classmethod
    async def list_nodes(
        cls,
        session,
        fuzzy_fields: dict[str, str] | None = None
    ) -> Sequence[Self]:
        """
        查询树节点列表

        Args:
            session: 数据库会话
            fuzzy_fields: 模糊查询字段 {字段名: 关键词}

        Returns:
            按 tree_sorts 排序的节点列表
        """
        stmt = select(cls)

        # 模糊查询
        if fuzzy_fields:
            conditions = []
            for field, keyword in fuzzy_fields.items():
                if hasattr(cls, field):
                    conditions.append(getattr(cls, field).contains(keyword))
            if conditions:
                stmt = stmt.where(or_(*conditions))

        # 按 tree_sorts 排序
        stmt = stmt.order_by(cls.tree_sorts)

        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    def build_tree(
        cls,
        nodes: Sequence[Self],
        parent_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        构建树结构

        Args:
            nodes: 平铺节点列表
            parent_id: 指定父节点ID，构建子树

        Returns:
            树形结构列表
        """
        parent_id = parent_id or DEFAULT_TREE_ROOT_ID

        # 将节点转换为字典
        def node_to_dict(node):
            if hasattr(node, "to_dict"):
                return node.to_dict()
            return {c.name: getattr(node, c.name) for c in node.__table__.columns}

        # 按父节点分组
        children_map: dict[str, list[dict[str, Any]]] = {}
        for node in nodes:
            pid = node.parent_id
            if pid not in children_map:
                children_map[pid] = []
            children_map[pid].append(node_to_dict(node))

        # 递归构建树
        def build_children(pid: str) -> list[dict[str, Any]]:
            tree = []
            for node_dict in children_map.get(pid, []):
                node_id = node_dict["id"]
                node_dict["children"] = build_children(node_id)
                tree.append(node_dict)
            return tree

        return build_children(parent_id)


# 向后兼容别名
TreeMixin = TreeNodeMixin
