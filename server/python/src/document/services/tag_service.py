"""标签服务"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Tag, TagGroup
from framework.common.ctx import get_tenant_id, get_user_id
from framework.permission.audit_writer import write_audit


class TagService:
    """标签服务"""

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        group_id: str | None = None,
        color: str | None = None,
        description: str | None = None,
        persona_id: str | None = None,
    ) -> Tag:
        """创建标签"""
        tenant_id = get_tenant_id()
        user_id = get_user_id()

        tag = Tag(
            tenant_id=tenant_id,
            name=name,
            group_id=group_id,
            color=color,
            description=description,
            persona_id=persona_id,
            status="active",
            doc_count=0,
        )
        session.add(tag)
        await session.flush()
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="create",
            resource_type="tag",
            resource_name=name,
        )
        return tag

    @staticmethod
    async def get_by_id(session: AsyncSession, tag_id: str) -> Tag | None:
        """按 ID 查询标签"""
        tenant_id = get_tenant_id()
        stmt = select(Tag).where(Tag.id == tag_id, Tag.tenant_id == tenant_id, Tag.status == "active")
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def delete(session: AsyncSession, tag_id: str) -> None:
        """删除标签（已被引用时拒绝）"""
        tenant_id = get_tenant_id()
        tag = await TagService.get_by_id(session, tag_id)
        if tag is None:
            raise ValueError("标签不存在")
        if tag.doc_count and tag.doc_count > 0:
            raise ValueError("标签已被文档引用，不可删除")
        if tag.persona_id:
            raise ValueError("标签被人设引用，不可删除")
        tag.status = "deleted"
        await session.flush()
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="delete",
            resource_type="tag",
            resource_name=tag_id,
        )

    @staticmethod
    async def list_tags(
        session: AsyncSession,
        tenant_id: str,
        group_id: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Tag], int]:
        """查询标签列表"""
        conditions = [Tag.tenant_id == tenant_id, Tag.status == "active"]
        if group_id:
            conditions.append(Tag.group_id == group_id)
        if keyword:
            conditions.append(Tag.name.like(f"%{keyword}%"))

        total = (await session.execute(
            select(func.count(Tag.id)).where(*conditions)
        )).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(Tag).where(*conditions)
            .order_by(Tag.created_at.desc())
            .offset(offset).limit(page_size)
        )
        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    @staticmethod
    async def list_groups(
        session: AsyncSession,
        tenant_id: str,
    ) -> list[TagGroup]:
        """查询标签分组列表"""
        stmt = (
            select(TagGroup)
            .where(TagGroup.tenant_id == tenant_id)
            .order_by(TagGroup.sort_order, TagGroup.created_at)
        )
        return list((await session.execute(stmt)).scalars().all())


tag_service = TagService()
