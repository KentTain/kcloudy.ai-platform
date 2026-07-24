"""人设服务（AI 提示词）"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Persona
from framework.common.ctx import get_tenant_id, get_user_id


class PersonaService:
    """人设服务"""

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        instruction: str,
        role: str | None = None,
        description: str | None = None,
    ) -> Persona:
        """创建人设（租户内名称唯一）"""
        tenant_id = get_tenant_id()
        user_id = get_user_id()

        # 名称租户内唯一校验
        if await PersonaService._has_name(session, tenant_id, name):
            raise ValueError("人设名称已存在")

        persona = Persona(
            tenant_id=tenant_id,
            name=name,
            instruction=instruction,
            role=role,
            description=description,
        )
        session.add(persona)
        await session.flush()
        return persona

    @staticmethod
    async def get_by_id(session: AsyncSession, persona_id: str) -> Persona | None:
        stmt = select(Persona).where(Persona.id == persona_id)
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def update(
        session: AsyncSession,
        persona_id: str,
        name: str | None = None,
        instruction: str | None = None,
        role: str | None = None,
        description: str | None = None,
    ) -> Persona:
        """更新人设"""
        persona = await PersonaService.get_by_id(session, persona_id)
        if persona is None:
            raise ValueError("人设不存在")

        if name is not None:
            # 名称唯一校验（排除自身）
            tenant_id = get_tenant_id()
            if await PersonaService._has_name(session, tenant_id, name, exclude_id=persona_id):
                raise ValueError("人设名称已存在")
            persona.name = name
        if instruction is not None:
            persona.instruction = instruction
        if role is not None:
            persona.role = role
        if description is not None:
            persona.description = description

        await session.flush()
        return persona

    @staticmethod
    async def delete(session: AsyncSession, persona_id: str) -> None:
        """删除人设"""
        persona = await PersonaService.get_by_id(session, persona_id)
        if persona is None:
            raise ValueError("人设不存在")
        await session.delete(persona)
        await session.flush()

    @staticmethod
    async def list_personas(
        session: AsyncSession,
        tenant_id: str,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Persona], int]:
        """查询人设列表"""
        conditions = [Persona.tenant_id == tenant_id]
        if keyword:
            conditions.append(Persona.name.like(f"%{keyword}%"))

        total = (await session.execute(
            select(func.count(Persona.id)).where(*conditions)
        )).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(Persona).where(*conditions)
            .order_by(Persona.created_at.desc())
            .offset(offset).limit(page_size)
        )
        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    @staticmethod
    async def list_options(session: AsyncSession, tenant_id: str) -> list[dict]:
        """获取人设选项列表（不含完整 instruction，用于下拉选择）"""
        stmt = (
            select(Persona.id, Persona.name, Persona.role, Persona.description)
            .where(Persona.tenant_id == tenant_id)
            .order_by(Persona.name)
        )
        result = await session.execute(stmt)
        return [
            {"id": row.id, "name": row.name, "role": row.role, "description": row.description}
            for row in result.all()
        ]

    @staticmethod
    async def _has_name(
        session: AsyncSession,
        tenant_id: str,
        name: str,
        exclude_id: str | None = None,
    ) -> bool:
        """检查名称是否已存在"""
        conditions = [Persona.tenant_id == tenant_id, Persona.name == name]
        if exclude_id:
            conditions.append(Persona.id != exclude_id)
        stmt = select(func.count(Persona.id)).where(*conditions)
        return (await session.execute(stmt)).scalar() > 0


persona_service = PersonaService()
