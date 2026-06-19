"""
Dataset Service
"""

from sqlalchemy import func, select

from framework.database.core.engine import async_session
from framework.tenant.context import get_tenant_id
from demo.models.dataset import Dataset
from demo.schemas.dataset import DatasetCreate, DatasetUpdate


class DatasetService:
    """知识库服务"""

    async def list_datasets(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[int, list[Dataset]]:
        """获取知识库列表（自动按当前租户过滤）"""
        tenant_id = get_tenant_id()
        async with async_session() as session:
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

    async def create_dataset(self, data: DatasetCreate) -> Dataset:
        """创建知识库（自动注入当前租户 ID）"""
        tenant_id = get_tenant_id()
        async with async_session() as session:
            try:
                create_data = data.model_dump()
                if tenant_id:
                    create_data["tenant_id"] = tenant_id
                dataset = await Dataset.create(session, create_data)
                await session.commit()
                return dataset
            except Exception as e:
                await session.rollback()
                raise e

    async def get_dataset(self, dataset_id: str) -> Dataset | None:
        """获取知识库详情"""
        tenant_id = get_tenant_id()
        async with async_session() as session:
            dataset = await Dataset.one_by_id(session, dataset_id)
            if tenant_id and dataset and dataset.tenant_id != tenant_id:
                return None
            return dataset

    async def update_dataset(
        self, dataset_id: str, data: DatasetUpdate
    ) -> Dataset | None:
        """更新知识库"""
        tenant_id = get_tenant_id()
        async with async_session() as session:
            try:
                dataset = await Dataset.one_by_id(session, dataset_id)
                if not dataset:
                    return None
                if tenant_id and dataset.tenant_id != tenant_id:
                    return None
                update_data = data.model_dump(exclude_unset=True)
                await dataset.update(session, update_data)
                await session.commit()
                return dataset
            except Exception as e:
                await session.rollback()
                raise e

    async def delete_dataset(self, dataset_id: str) -> bool:
        """删除知识库"""
        tenant_id = get_tenant_id()
        async with async_session() as session:
            try:
                dataset = await Dataset.one_by_id(session, dataset_id)
                if not dataset:
                    return False
                if tenant_id and dataset.tenant_id != tenant_id:
                    return False
                await session.delete(dataset)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e


dataset_service = DatasetService()
