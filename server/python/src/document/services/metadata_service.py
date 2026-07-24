"""元数据服务"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import LibraryMetadataField, ResourceMetadata
from document.models.enums import MetadataFieldType
from framework.common.ctx import get_tenant_id, get_user_id


class MetadataService:
    """元数据服务"""

    @staticmethod
    async def define_field(
        session: AsyncSession,
        library_id: str,
        name: str,
        field_type: str,
        is_required: bool = False,
        enum_values: list[str] | None = None,
        sort_order: int = 0,
    ) -> LibraryMetadataField:
        """定义元数据字段"""
        tenant_id = get_tenant_id()

        field = LibraryMetadataField(
            tenant_id=tenant_id,
            library_id=library_id,
            name=name,
            field_type=field_type,
            is_required=is_required,
            enum_values=enum_values,
            sort_order=sort_order,
        )
        session.add(field)
        await session.flush()
        return field

    @staticmethod
    async def set_metadata(
        session: AsyncSession,
        library_id: str,
        resource_type: str,
        resource_id: str,
        field_id: str,
        field_name: str,
        value: str | None = None,
    ) -> ResourceMetadata:
        """设置资源元数据（枚举值校验）"""
        tenant_id = get_tenant_id()

        # 枚举值校验
        if value is not None:
            field_def = await MetadataService.get_field(session, field_id)
            if field_def and field_def.field_type == MetadataFieldType.ENUM:
                allowed = field_def.enum_values or []
                if value not in allowed:
                    raise ValueError(f"枚举值 {value} 不在允许范围内: {allowed}")

        # 查找已有记录或创建新记录
        stmt = select(ResourceMetadata).where(
            ResourceMetadata.resource_id == resource_id,
            ResourceMetadata.field_id == field_id,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.value = value
            await session.flush()
            return existing

        metadata = ResourceMetadata(
            tenant_id=tenant_id,
            library_id=library_id,
            resource_type=resource_type,
            resource_id=resource_id,
            field_id=field_id,
            field_name=field_name,
            value=value,
        )
        session.add(metadata)
        await session.flush()
        return metadata

    @staticmethod
    async def batch_set(
        session: AsyncSession,
        library_id: str,
        resource_type: str,
        resource_id: str,
        items: list[dict],
    ) -> list[ResourceMetadata]:
        """批量设置元数据"""
        results = []
        for item in items:
            result = await MetadataService.set_metadata(
                session=session,
                library_id=library_id,
                resource_type=resource_type,
                resource_id=resource_id,
                field_id=item["field_id"],
                field_name=item["field_name"],
                value=item.get("value"),
            )
            results.append(result)
        return results

    @staticmethod
    async def query_metadata(
        session: AsyncSession,
        library_id: str,
        resource_type: str,
        resource_id: str,
    ) -> list[ResourceMetadata]:
        """查询资源元数据"""
        stmt = select(ResourceMetadata).where(
            ResourceMetadata.library_id == library_id,
            ResourceMetadata.resource_type == resource_type,
            ResourceMetadata.resource_id == resource_id,
        )
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def search_by_metadata(
        session: AsyncSession,
        library_id: str,
        field_name: str,
        value: str,
        resource_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ResourceMetadata], int]:
        """按元数据搜索资源"""
        conditions = [
            ResourceMetadata.library_id == library_id,
            ResourceMetadata.field_name == field_name,
            ResourceMetadata.value == value,
        ]
        if resource_type:
            conditions.append(ResourceMetadata.resource_type == resource_type)

        total = (await session.execute(
            select(func.count(ResourceMetadata.id)).where(*conditions)
        )).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(ResourceMetadata).where(*conditions)
            .offset(offset).limit(page_size)
        )
        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    @staticmethod
    async def get_field(session: AsyncSession, field_id: str) -> LibraryMetadataField | None:
        """获取元数据字段定义"""
        stmt = select(LibraryMetadataField).where(LibraryMetadataField.id == field_id)
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def list_fields(
        session: AsyncSession,
        library_id: str,
    ) -> list[LibraryMetadataField]:
        """查询文档库的元数据字段列表"""
        stmt = (
            select(LibraryMetadataField)
            .where(LibraryMetadataField.library_id == library_id)
            .order_by(LibraryMetadataField.sort_order, LibraryMetadataField.created_at)
        )
        return list((await session.execute(stmt)).scalars().all())


metadata_service = MetadataService()
