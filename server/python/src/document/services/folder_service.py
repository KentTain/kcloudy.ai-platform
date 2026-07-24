"""文件夹服务（基于 TreeNodeMixin）"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Folder
from framework.common.ctx import get_tenant_id


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
        return folder

    @staticmethod
    async def rename(session: AsyncSession, folder_id: str, name: str) -> Folder:
        """重命名文件夹"""
        tenant_id = get_tenant_id()
        return await Folder.update_node(
            session,
            id=folder_id,
            source={"name": name},
            extra_conditions=[Folder.tenant_id == tenant_id],
        )

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

        return await Folder.update_node(
            session,
            id=folder_id,
            source={"parent_id": new_parent_id},
            extra_conditions=extra_conditions,
        )

    @staticmethod
    async def delete(session: AsyncSession, folder_id: str) -> int:
        """删除文件夹（软删除，含子孙）"""
        tenant_id = get_tenant_id()
        return await Folder.delete_node(
            session,
            id=folder_id,
            extra_conditions=[Folder.tenant_id == tenant_id],
        )

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
