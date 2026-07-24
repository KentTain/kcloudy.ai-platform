"""文档库服务"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Library, LibraryMember
from document.models.enums import LibraryMemberRole, LibraryMemberStatus, LibraryType
from framework.common.ctx import get_tenant_id, get_user_id
from framework.permission.audit_writer import write_audit


class LibraryService:
    """文档库服务"""

    @staticmethod
    async def create(
        session: AsyncSession,
        library_type: str,
        code: str,
        name: str,
        description: str | None = None,
        icon: str | None = None,
    ) -> Library:
        """创建文档库"""
        tenant_id = get_tenant_id()
        user_id = get_user_id()

        # 个人文档库唯一性校验
        if library_type == LibraryType.PERSONAL:
            if await LibraryService.has_personal_library(session, tenant_id=tenant_id, user_id=user_id):
                raise ValueError("每个用户最多一个个人文档库")

        # 团队文档库名称唯一性校验
        if library_type == LibraryType.TEAM:
            if await LibraryService.has_team_library_name(session, tenant_id=tenant_id, name=name):
                raise ValueError("文档库名称已存在")

        library = Library(
            tenant_id=tenant_id,
            type=library_type,
            code=code,
            name=name,
            description=description,
            icon=icon,
            owner_id=user_id,
            enabled=True,
            allow_submit_to_kb=True,
        )
        session.add(library)
        await session.flush()
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="create",
            resource_type="library",
            resource_name=name,
        )

        # 创建者自动成为 owner
        member = LibraryMember(
            tenant_id=tenant_id,
            library_id=library.id,
            user_id=user_id,
            user_name=user_id,  # 实际应从 iam 查询用户名
            role=LibraryMemberRole.OWNER,
            status=LibraryMemberStatus.ACTIVE,
        )
        session.add(member)
        await session.flush()
        return library

    @staticmethod
    async def has_personal_library(session: AsyncSession, tenant_id: str, user_id: str) -> bool:
        """是否已有个人文档库"""
        stmt = select(func.count(Library.id)).where(
            Library.tenant_id == tenant_id,
            Library.owner_id == user_id,
            Library.type == LibraryType.PERSONAL,
            Library.enabled.is_(True),
        )
        return (await session.execute(stmt)).scalar() > 0

    @staticmethod
    async def has_team_library_name(session: AsyncSession, tenant_id: str, name: str) -> bool:
        stmt = select(func.count(Library.id)).where(
            Library.tenant_id == tenant_id,
            Library.name == name,
            Library.type == LibraryType.TEAM,
            Library.enabled.is_(True),
        )
        return (await session.execute(stmt)).scalar() > 0

    @staticmethod
    async def list_libraries(
        session: AsyncSession,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        library_type: str | None = None,
    ) -> tuple[list[Library], int]:
        conditions = [Library.tenant_id == tenant_id, Library.enabled.is_(True)]
        if keyword:
            conditions.append(Library.name.like(f"%{keyword}%"))
        if library_type:
            conditions.append(Library.type == library_type)

        total = (await session.execute(
            select(func.count(Library.id)).where(*conditions)
        )).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(Library).where(*conditions)
            .order_by(Library.created_at.desc())
            .offset(offset).limit(page_size)
        )
        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    @staticmethod
    async def get_by_id(session: AsyncSession, library_id: str) -> Library | None:
        tenant_id = get_tenant_id()
        stmt = select(Library).where(
            Library.id == library_id,
            Library.tenant_id == tenant_id,
            Library.enabled.is_(True),
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def update(
        session: AsyncSession,
        library_id: str,
        name: str | None = None,
        description: str | None = None,
        icon: str | None = None,
        enabled: bool | None = None,
        allow_submit_to_kb: bool | None = None,
    ) -> Library:
        """更新文档库"""
        lib = await LibraryService.get_by_id(session, library_id)
        if lib is None:
            raise ValueError("文档库不存在")
        if name is not None:
            lib.name = name
        if description is not None:
            lib.description = description
        if icon is not None:
            lib.icon = icon
        if enabled is not None:
            lib.enabled = enabled
        if allow_submit_to_kb is not None:
            lib.allow_submit_to_kb = allow_submit_to_kb
        await session.flush()
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="update",
            resource_type="library",
            resource_name=lib.name,
            resource_id=library_id,
        )
        return lib

    @staticmethod
    async def soft_delete(session: AsyncSession, library_id: str) -> None:
        """软删除文档库（设 enabled=False）"""
        lib = await LibraryService.get_by_id(session, library_id)
        if lib is None:
            raise ValueError("文档库不存在")
        lib.enabled = False
        await session.flush()
        await write_audit(
            session=session,
            business_domain="document",
            operation_type="delete",
            resource_type="library",
            resource_name=lib.name,
            resource_id=library_id,
        )


library_service = LibraryService()
