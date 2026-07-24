"""回收站服务"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Document, Folder, RecycleItem
from document.models.enums import FolderLifecycleStatus, RecycleItemStatus, ResourceType
from framework.common.ctx import get_tenant_id, get_user_id
from framework.permission.audit_writer import write_audit


class RecycleService:
    """回收站服务"""

    @staticmethod
    async def add_to_recycle(
        session: AsyncSession,
        library_id: str,
        resource_type: str,
        resource_id: str,
        original_parent_id: str | None = None,
        original_path: str | None = None,
    ) -> RecycleItem:
        """将资源添加到回收站"""
        tenant_id = get_tenant_id()
        user_id = get_user_id()

        item = RecycleItem(
            tenant_id=tenant_id,
            library_id=library_id,
            resource_type=resource_type,
            resource_id=resource_id,
            original_parent_id=original_parent_id,
            original_path=original_path,
            deleted_by=user_id,
            status=RecycleItemStatus.IN_RECYCLE,
        )
        session.add(item)
        await session.flush()
        return item

    @staticmethod
    async def list_items(
        session: AsyncSession,
        library_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[RecycleItem], int]:
        """查看回收站列表"""
        tenant_id = get_tenant_id()
        conditions = [
            RecycleItem.library_id == library_id,
            RecycleItem.tenant_id == tenant_id,
            RecycleItem.status == RecycleItemStatus.IN_RECYCLE,
        ]
        total = (await session.execute(
            select(func.count(RecycleItem.id)).where(*conditions)
        )).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(RecycleItem).where(*conditions)
            .order_by(RecycleItem.created_at.desc())
            .offset(offset).limit(page_size)
        )
        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    @staticmethod
    async def restore(session: AsyncSession, item_id: str) -> None:
        """恢复回收站项目

        恢复逻辑：
          1. 检查 original_parent_id 是否仍存在（Folder/Document 查询）
          2. 如果不存在，恢复到库根（folder_id=None / parent_id="root"）
          3. 名称冲突时追加后缀 "_restored"
        """
        item = await RecycleService._get_item(session, item_id)
        if item is None:
            raise ValueError("回收站项目不存在")

        # 检查原父资源是否仍存在
        parent_exists = await RecycleService._check_parent_exists(session, item)

        if not parent_exists:
            # 原父资源已不存在，恢复到库根
            await RecycleService._restore_to_root(session, item)
        else:
            # 原父资源存在，检查名称冲突
            await RecycleService._restore_with_name_check(session, item)

        user_id = get_user_id()
        item.status = RecycleItemStatus.RESTORED
        item.restored_by = user_id
        item.restored_at = datetime.now(timezone.utc)
        await session.flush()
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="restore",
            resource_type="recycle_item",
            resource_name=item_id,
        )

    @staticmethod
    async def _check_parent_exists(session: AsyncSession, item: RecycleItem) -> bool:
        """检查 original_parent_id 对应的资源是否仍存在"""
        if item.original_parent_id is None:
            return True  # 无父资源，视为根目录
        if item.resource_type in (ResourceType.DOCUMENT, ResourceType.FOLDER):
            # 文档和文件夹的父资源都是文件夹
            tenant_id = get_tenant_id()
            stmt = select(Folder).where(
                Folder.id == item.original_parent_id,
                Folder.tenant_id == tenant_id,
                Folder.lifecycle_status == FolderLifecycleStatus.ACTIVE,
            )
            result = (await session.execute(stmt)).scalar_one_or_none()
            return result is not None
        return False

    @staticmethod
    async def _restore_to_root(session: AsyncSession, item: RecycleItem) -> None:
        """恢复到库根目录（folder_id=None / parent_id="root"）"""
        tenant_id = get_tenant_id()
        if item.resource_type == ResourceType.DOCUMENT:
            stmt = select(Document).where(
                Document.id == item.resource_id,
                Document.tenant_id == tenant_id,
            )
            doc = (await session.execute(stmt)).scalar_one_or_none()
            if doc is not None:
                doc.folder_id = None
        elif item.resource_type == ResourceType.FOLDER:
            stmt = select(Folder).where(
                Folder.id == item.resource_id,
                Folder.tenant_id == tenant_id,
            )
            folder = (await session.execute(stmt)).scalar_one_or_none()
            if folder is not None:
                folder.parent_id = "root"

    @staticmethod
    async def _restore_with_name_check(session: AsyncSession, item: RecycleItem) -> None:
        """恢复到原位置，名称冲突时追加后缀 '_restored'"""
        tenant_id = get_tenant_id()
        if item.resource_type == ResourceType.DOCUMENT:
            stmt = select(Document).where(
                Document.id == item.resource_id,
                Document.tenant_id == tenant_id,
            )
            doc = (await session.execute(stmt)).scalar_one_or_none()
            if doc is None:
                return
            # 检查同文件夹下同名文档
            name_exists = await RecycleService._check_doc_name_conflict(session, doc)
            if name_exists:
                doc.name = f"{doc.name}_restored"
        elif item.resource_type == ResourceType.FOLDER:
            stmt = select(Folder).where(
                Folder.id == item.resource_id,
                Folder.tenant_id == tenant_id,
            )
            folder = (await session.execute(stmt)).scalar_one_or_none()
            if folder is None:
                return
            # 检查同父文件夹下同名文件夹
            name_exists = await RecycleService._check_folder_name_conflict(session, folder)
            if name_exists:
                folder.name = f"{folder.name}_restored"

    @staticmethod
    async def _check_doc_name_conflict(session: AsyncSession, doc: Document) -> bool:
        """检查文档名称是否在同文件夹下冲突"""
        tenant_id = get_tenant_id()
        conditions = [
            Document.folder_id == doc.folder_id,
            Document.name == doc.name,
            Document.id != doc.id,
            Document.tenant_id == tenant_id,
        ]
        stmt = select(func.count(Document.id)).where(*conditions)
        return (await session.execute(stmt)).scalar() > 0

    @staticmethod
    async def _check_folder_name_conflict(session: AsyncSession, folder: Folder) -> bool:
        """检查文件夹名称是否在同父级下冲突"""
        tenant_id = get_tenant_id()
        conditions = [
            Folder.parent_id == folder.parent_id,
            Folder.name == folder.name,
            Folder.id != folder.id,
            Folder.tenant_id == tenant_id,
        ]
        stmt = select(func.count(Folder.id)).where(*conditions)
        return (await session.execute(stmt)).scalar() > 0

    @staticmethod
    async def purge(session: AsyncSession, item_id: str) -> None:
        """永久删除回收站项目"""
        item = await RecycleService._get_item(session, item_id)
        if item is None:
            raise ValueError("回收站项目不存在")
        item.status = RecycleItemStatus.PURGED
        await session.flush()
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="purge",
            resource_type="recycle_item",
            resource_name=item_id,
        )

    @staticmethod
    async def clear(session: AsyncSession, library_id: str) -> int:
        """清空回收站"""
        tenant_id = get_tenant_id()
        stmt = select(RecycleItem).where(
            RecycleItem.library_id == library_id,
            RecycleItem.tenant_id == tenant_id,
            RecycleItem.status == RecycleItemStatus.IN_RECYCLE,
        )
        result = await session.execute(stmt)
        items = list(result.scalars().all())
        for item in items:
            item.status = RecycleItemStatus.PURGED
        await session.flush()
        count = len(items)
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="purge",
            resource_type="recycle_item",
            resource_name=library_id,
            detail={"cleared_count": count},
        )
        return count

    @staticmethod
    async def _get_item(session: AsyncSession, item_id: str) -> RecycleItem | None:
        """获取回收站项目"""
        tenant_id = get_tenant_id()
        stmt = select(RecycleItem).where(
            RecycleItem.id == item_id,
            RecycleItem.tenant_id == tenant_id,
            RecycleItem.status == RecycleItemStatus.IN_RECYCLE,
        )
        return (await session.execute(stmt)).scalar_one_or_none()


recycle_service = RecycleService()
