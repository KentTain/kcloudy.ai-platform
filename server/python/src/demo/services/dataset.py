"""
Dataset Service
"""

from sqlalchemy import func, select

from demo.models.core.engine import async_session
from demo.models.dataset import Dataset
from demo.schemas.dataset import DatasetCreate, DatasetUpdate


class DatasetService:
    """知识库服务"""

    async def list_datasets(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[int, list[Dataset]]:
        """获取知识库列表"""
        async with async_session() as session:
            # 查询总数
            count_stmt = select(func.count()).select_from(Dataset)
            total = (await session.execute(count_stmt)).scalar() or 0

            # 查询列表
            offset = (page - 1) * page_size
            stmt = (
                select(Dataset)
                .offset(offset)
                .limit(page_size)
                .order_by(Dataset.created_at.desc())
            )
            result = await session.execute(stmt)
            datasets = list(result.scalars().all())

            return total, datasets

    async def create_dataset(self, data: DatasetCreate) -> Dataset:
        """创建知识库"""
        async with async_session() as session:
            try:
                dataset = await Dataset.create(session, data.model_dump())
                await session.commit()
                return dataset
            except Exception as e:
                await session.rollback()
                raise e

    async def get_dataset(self, dataset_id: str) -> Dataset | None:
        """获取知识库详情"""
        async with async_session() as session:
            return await Dataset.one_by_id(session, dataset_id)

    async def update_dataset(
        self, dataset_id: str, data: DatasetUpdate
    ) -> Dataset | None:
        """更新知识库"""
        async with async_session() as session:
            try:
                dataset = await Dataset.one_by_id(session, dataset_id)
                if not dataset:
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
        async with async_session() as session:
            try:
                dataset = await Dataset.one_by_id(session, dataset_id)
                if not dataset:
                    return False
                await session.delete(dataset)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e


dataset_service = DatasetService()
