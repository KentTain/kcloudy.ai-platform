"""文档库成员服务"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import LibraryMember
from document.models.enums import LibraryMemberRole, LibraryMemberStatus
from framework.common.ctx import get_tenant_id, get_user_id


class MemberService:
    """文档库成员服务"""

    @staticmethod
    async def add_member(
        session: AsyncSession,
        library_id: str,
        user_id: str,
        user_name: str,
        role: str = LibraryMemberRole.MEMBER,
        remarks: str | None = None,
    ) -> LibraryMember:
        """添加成员

        跨租户校验在控制器层通过 iam inner 接口完成
        （service 层不直接调用 iam），当前仅校验重复成员。
        """
        tenant_id = get_tenant_id()

        # 检查是否已是成员
        existing = await MemberService.get_member(session, library_id, user_id)
        if existing is not None:
            raise ValueError("用户已是文档库成员")

        member = LibraryMember(
            tenant_id=tenant_id,
            library_id=library_id,
            user_id=user_id,
            user_name=user_name,
            role=role,
            status=LibraryMemberStatus.ACTIVE,
            remarks=remarks,
        )
        session.add(member)
        await session.flush()
        return member

    @staticmethod
    async def remove_member(session: AsyncSession, library_id: str, user_id: str) -> None:
        """移除成员（owner 不可移除）"""
        member = await MemberService.get_member(session, library_id, user_id)
        if member is None:
            raise ValueError("成员不存在")
        if member.role == LibraryMemberRole.OWNER:
            raise ValueError("不能移除 owner")
        member.status = LibraryMemberStatus.INACTIVE
        await session.flush()

    @staticmethod
    async def update_member_role(
        session: AsyncSession,
        library_id: str,
        user_id: str,
        new_role: str,
    ) -> LibraryMember:
        """更新成员角色"""
        member = await MemberService.get_member(session, library_id, user_id)
        if member is None:
            raise ValueError("成员不存在")
        if member.role == LibraryMemberRole.OWNER:
            raise ValueError("不能修改 owner 角色")
        member.role = new_role
        await session.flush()
        return member

    @staticmethod
    async def get_member(
        session: AsyncSession,
        library_id: str,
        user_id: str,
    ) -> LibraryMember | None:
        """获取成员信息"""
        stmt = select(LibraryMember).where(
            LibraryMember.library_id == library_id,
            LibraryMember.user_id == user_id,
            LibraryMember.status == LibraryMemberStatus.ACTIVE,
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def list_members(
        session: AsyncSession,
        library_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[LibraryMember], int]:
        """列出文档库成员"""
        conditions = [
            LibraryMember.library_id == library_id,
            LibraryMember.status == LibraryMemberStatus.ACTIVE,
        ]
        total = (await session.execute(
            select(func.count(LibraryMember.id)).where(*conditions)
        )).scalar() or 0
        offset = (page - 1) * page_size
        stmt = (
            select(LibraryMember).where(*conditions)
            .offset(offset).limit(page_size)
        )
        return list((await session.execute(stmt)).scalars().all()), total


member_service = MemberService()
