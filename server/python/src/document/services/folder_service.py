"""文件夹服务（基于 TreeNodeMixin）"""

import sqlalchemy
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Folder, RecycleItem
from document.models.enums import FolderLifecycleStatus, ResourceType
from framework.common.ctx import get_tenant_id, get_user_id
from framework.permission.audit_writer import write_audit


class FolderService:
    """文件夹服务"""

    @staticmethod
    async def create(
        session: AsyncSession,
        library_id: str,
        name: str,
        parent_id: str | None = None,
        description: str | None = None,
    ) -> Folder:
        """创建文件夹（使用 TreeNodeMixin.create_node 自动维护树字段）"""
        tenant_id = get_tenant_id()
        folder = await Folder.create_node(
            session,
            source={
                "library_id": library_id,
                "name": name,
                "description": description,
                "parent_id": parent_id,
                "tenant_id": tenant_id,
            },
            extra_conditions=[Folder.tenant_id == tenant_id],
        )
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="create",
            resource_type="folder",
            resource_name=name,
        )
        return folder

    @staticmethod
    async def rename(session: AsyncSession, folder_id: str, name: str) -> Folder:
        """重命名文件夹"""
        tenant_id = get_tenant_id()
        folder = await Folder.update_node(
            session,
            id=folder_id,
            source={"name": name},
            extra_conditions=[Folder.tenant_id == tenant_id],
        )
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="update",
            resource_type="folder",
            resource_name=name,
            resource_id=folder_id,
        )
        return folder

    @staticmethod
    async def move(session: AsyncSession, folder_id: str, new_parent_id: str) -> Folder:
        """移动文件夹（循环引用检测）

        检测逻辑：如果目标父节点的 parent_ids 包含当前节点 ID，
        则目标是当前节点的子孙，移动会形成循环引用。
        """
        tenant_id = get_tenant_id()
        extra_conditions = [Folder.tenant_id == tenant_id]

        if new_parent_id and new_parent_id != Folder.get_root_id():
            # 查询目标父节点
            target = await Folder.one_node(session, new_parent_id, extra_conditions)
            if target is None:
                raise ValueError("目标文件夹不存在")

            # 查询当前节点
            current = await Folder.one_node(session, folder_id, extra_conditions)
            if current is None:
                raise ValueError("文件夹不存在")

            # 检测循环引用：目标的 parent_ids 是否包含当前节点
            # 即目标的祖先链中是否包含当前节点
            current_descendant_prefix = f"{current.parent_ids}{current.id},"
            if target.parent_ids.startswith(current_descendant_prefix):
                raise ValueError("不允许形成循环引用")

        result = await Folder.update_node(
            session,
            id=folder_id,
            source={"parent_id": new_parent_id},
            extra_conditions=extra_conditions,
        )
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="move",
            resource_type="folder",
            resource_name="",
            resource_id=folder_id,
        )
        return result

    @staticmethod
    async def delete(session: AsyncSession, folder_id: str) -> str:
        """软删除文件夹及所有子孙（lifecycle_status=TRASHED），并创建回收站记录"""
        tenant_id = get_tenant_id()
        folder = await Folder.one_node(
            session, folder_id, extra_conditions=[Folder.tenant_id == tenant_id]
        )
        if not folder:
            raise ValueError("文件夹不存在")

        # 软删除：将 folder 及所有子孙的 lifecycle_status 设为 TRASHED
        descendant_prefix = folder.descendant_parent_ids_prefix()
        conditions = [
            Folder.tenant_id == tenant_id,
            Folder.lifecycle_status == FolderLifecycleStatus.ACTIVE,
            sqlalchemy.or_(
                Folder.id == folder_id,
                Folder.parent_ids.like(f"{descendant_prefix}%"),
            ),
        ]
        await session.execute(
            sa_update(Folder)
            .where(*conditions)
            .values(lifecycle_status=FolderLifecycleStatus.TRASHED)
        )

        # 创建回收站记录
        recycle_item = RecycleItem(
            library_id=folder.library_id,
            resource_type=ResourceType.FOLDER,
            resource_id=folder_id,
            original_parent_id=folder.parent_id if not folder.is_root_node() else None,
            original_path=folder.tree_names,
            deleted_by=get_user_id(),
            tenant_id=tenant_id,
        )
        session.add(recycle_item)
        await session.flush()
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="delete",
            resource_type="folder",
            resource_name="",
            resource_id=folder_id,
        )
        return recycle_item.id

    @staticmethod
    async def list_tree(session: AsyncSession, library_id: str) -> list:
        """获取文件夹树"""
        tenant_id = get_tenant_id()
        nodes = await Folder.list_nodes(
            session,
            extra_conditions=[Folder.library_id == library_id, Folder.tenant_id == tenant_id],
        )
        return Folder.build_tree(nodes)


folder_service = FolderService()
