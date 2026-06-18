"""
Dataset Service

使用依赖注入模式，session 由 Controller 层注入。
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.tenant.context import get_tenant_id
from demo.models.dataset import Dataset
from demo.schemas.dataset import DatasetCreate, DatasetUpdate


class DatasetService:
    """知识库服务"""

    async def list_datasets(
        self, session: AsyncSession, page: int = 1, page_size: int = 10
    ) -> tuple[int, list[Dataset]]:
        """
        获取知识库列表（自动按当前租户过滤）

        Args:
            session: 数据库会话（由 Controller 注入）
            page: 页码
            page_size: 每页数量
        """
        tenant_id = get_tenant_id()

        # 查询总数
        count_stmt = select(func.count()).select_from(Dataset)
        if tenant_id:
            count_stmt = count_stmt.where(Dataset.tenant_id == tenant_id)
        total = (await session.execute(count_stmt)).scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = (
            select(Dataset)
            .offset(offset)
            .limit(page_size)
            .order_by(Dataset.created_at.desc())
        )
        if tenant_id:
            stmt = stmt.where(Dataset.tenant_id == tenant_id)
        result = await session.execute(stmt)
        datasets = list(result.scalars().all())

        return total, datasets

    async def create_dataset(self, session: AsyncSession, data: DatasetCreate) -> Dataset:
        """
        创建知识库（自动注入当前租户 ID）

        Args:
            session: 数据库会话（由 Controller 注入）
            data: 创建数据
        """
        tenant_id = get_tenant_id()
        create_data = data.model_dump()
        if tenant_id:
            create_data["tenant_id"] = tenant_id
        dataset = await Dataset.create(session, create_data)
        await session.flush()
        return dataset

    async def get_dataset(self, session: AsyncSession, dataset_id: str) -> Dataset | None:
        """
        获取知识库详情

        Args:
            session: 数据库会话（由 Controller 注入）
            dataset_id: 知识库 ID
        """
        tenant_id = get_tenant_id()
        dataset = await Dataset.one_by_id(session, dataset_id)
        if tenant_id and dataset and dataset.tenant_id != tenant_id:
            return None
        return dataset

    async def update_dataset(
        self, session: AsyncSession, dataset_id: str, data: DatasetUpdate
    ) -> Dataset | None:
        """
        更新知识库

        Args:
            session: 数据库会话（由 Controller 注入）
            dataset_id: 知识库 ID
            data: 更新数据
        """
        tenant_id = get_tenant_id()
        dataset = await Dataset.one_by_id(session, dataset_id)
        if not dataset:
            return None
        if tenant_id and dataset.tenant_id != tenant_id:
            return None
        update_data = data.model_dump(exclude_unset=True)
        await dataset.update(session, update_data)
        await session.flush()
        return dataset

    async def delete_dataset(self, session: AsyncSession, dataset_id: str) -> bool:
        """
        删除知识库

        Args:
            session: 数据库会话（由 Controller 注入）
            dataset_id: 知识库 ID
        """
        tenant_id = get_tenant_id()
        dataset = await Dataset.one_by_id(session, dataset_id)
        if not dataset:
            return False
        if tenant_id and dataset.tenant_id != tenant_id:
            return False
        await session.delete(dataset)
        await session.flush()
        return True


dataset_service = DatasetService()
