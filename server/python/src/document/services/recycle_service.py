"""回收站服务"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import RecycleItem
from document.models.enums import RecycleItemStatus
from framework.common.ctx import get_tenant_id, get_user_id


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
        conditions = [
            RecycleItem.library_id == library_id,
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
        """恢复回收站项目"""
        item = await RecycleService._get_item(session, item_id)
        if item is None:
            raise ValueError("回收站项目不存在")
        user_id = get_user_id()
        item.status = RecycleItemStatus.RESTORED
        item.restored_by = user_id
        item.restored_at = datetime.now(timezone.utc)
        await session.flush()

    @staticmethod
    async def purge(session: AsyncSession, item_id: str) -> None:
        """永久删除回收站项目"""
        item = await RecycleService._get_item(session, item_id)
        if item is None:
            raise ValueError("回收站项目不存在")
        item.status = RecycleItemStatus.PURGED
        await session.flush()

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
        return len(items)

    @staticmethod
    async def _get_item(session: AsyncSession, item_id: str) -> RecycleItem | None:
        """获取回收站项目"""
        stmt = select(RecycleItem).where(
            RecycleItem.id == item_id,
            RecycleItem.status == RecycleItemStatus.IN_RECYCLE,
        )
        return (await session.execute(stmt)).scalar_one_or_none()


recycle_service = RecycleService()
