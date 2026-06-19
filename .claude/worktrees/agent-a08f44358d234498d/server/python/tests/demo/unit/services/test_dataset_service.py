"""DatasetService 单元测试"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from demo.schemas.dataset import DatasetCreate, DatasetUpdate
from demo.services.dataset import DatasetService


@pytest.fixture
def mock_session() -> AsyncMock:
    """创建模拟的数据库会话（AsyncSession 的 Mock）"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.delete = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def dataset_service() -> DatasetService:
    """创建 DatasetService 实例"""
    return DatasetService()


@pytest.fixture
def mock_dataset() -> MagicMock:
    """创建模拟的 Dataset 模型实例"""
    dataset = MagicMock()
    dataset.id = "test-dataset-id"
    dataset.name = "测试知识库"
    dataset.description = "测试描述"
    return dataset


class TestDatasetService:
    """DatasetService 单元测试"""

    @pytest.mark.asyncio
    async def test_list_datasets(self, mock_session):
        """测试返回知识库列表"""
        # Mock execute 返回结果
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_datasets_result = MagicMock()
        mock_datasets = [MagicMock(id="1"), MagicMock(id="2")]
        mock_datasets_result.scalars.return_value.all.return_value = mock_datasets

        mock_session.execute.side_effect = [mock_count_result, mock_datasets_result]
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            service = DatasetService()
            total, datasets = await service.list_datasets(page=1, page_size=10)

        assert total == 2
        assert len(datasets) == 2

    @pytest.mark.asyncio
    async def test_create_dataset(self, mock_session, mock_dataset):
        """测试创建知识库"""
        data = DatasetCreate(name="测试知识库", description="测试描述")
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "demo.services.dataset.Dataset.create", return_value=mock_dataset
            ):
                service = DatasetService()
                result = await service.create_dataset(data)

        assert result == mock_dataset
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_dataset_rollback_on_error(self, mock_session):
        """测试创建知识库时异常回滚"""
        data = DatasetCreate(name="测试知识库", description="测试描述")
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "demo.services.dataset.Dataset.create",
                side_effect=Exception("DB Error"),
            ):
                service = DatasetService()
                with pytest.raises(Exception, match="DB Error"):
                    await service.create_dataset(data)

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_dataset_found(self, mock_session, mock_dataset):
        """测试获取知识库 - 存在"""
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "demo.services.dataset.Dataset.one_by_id", return_value=mock_dataset
            ), patch("demo.services.dataset.get_tenant_id", return_value=None):
                service = DatasetService()
                result = await service.get_dataset("test-dataset-id")

        assert result == mock_dataset

    @pytest.mark.asyncio
    async def test_get_dataset_not_found(self, mock_session):
        """测试获取知识库 - 不存在"""
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("demo.services.dataset.Dataset.one_by_id", return_value=None), patch(
                "demo.services.dataset.get_tenant_id", return_value=None
            ):
                service = DatasetService()
                result = await service.get_dataset("nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_dataset_found(self, mock_session, mock_dataset):
        """测试更新知识库 - 存在"""
        data = DatasetUpdate(name="更新后的名称", description="更新后的描述")
        mock_dataset.update = AsyncMock()
        mock_dataset.tenant_id = None  # 避免租户隔离检查
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "demo.services.dataset.Dataset.one_by_id", return_value=mock_dataset
            ), patch("demo.services.dataset.get_tenant_id", return_value=None):
                service = DatasetService()
                result = await service.update_dataset("test-dataset-id", data)

        assert result == mock_dataset
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_dataset_not_found(self, mock_session):
        """测试更新知识库 - 不存在"""
        data = DatasetUpdate(name="更新后的名称", description=None)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("demo.services.dataset.Dataset.one_by_id", return_value=None), patch(
                "demo.services.dataset.get_tenant_id", return_value=None
            ):
                service = DatasetService()
                result = await service.update_dataset("nonexistent-id", data)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_dataset_rollback_on_error(self, mock_session, mock_dataset):
        """测试更新知识库时异常回滚"""
        data = DatasetUpdate(name="更新后的名称", description=None)
        mock_dataset.update = AsyncMock(side_effect=Exception("Update Error"))
        mock_dataset.tenant_id = None  # 避免租户隔离检查
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "demo.services.dataset.Dataset.one_by_id", return_value=mock_dataset
            ), patch("demo.services.dataset.get_tenant_id", return_value=None):
                service = DatasetService()
                with pytest.raises(Exception, match="Update Error"):
                    await service.update_dataset("test-dataset-id", data)

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_dataset_found(self, mock_session, mock_dataset):
        """测试删除知识库 - 存在"""
        mock_dataset.tenant_id = None  # 避免租户隔离检查
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "demo.services.dataset.Dataset.one_by_id", return_value=mock_dataset
            ), patch("demo.services.dataset.get_tenant_id", return_value=None):
                service = DatasetService()
                result = await service.delete_dataset("test-dataset-id")

        assert result is True
        mock_session.delete.assert_called_once_with(mock_dataset)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_dataset_not_found(self, mock_session):
        """测试删除知识库 - 不存在"""
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("demo.services.dataset.Dataset.one_by_id", return_value=None), patch(
                "demo.services.dataset.get_tenant_id", return_value=None
            ):
                service = DatasetService()
                result = await service.delete_dataset("nonexistent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_dataset_rollback_on_error(self, mock_session, mock_dataset):
        """测试删除知识库时异常回滚"""
        mock_dataset.tenant_id = None  # 避免租户隔离检查
        mock_session.delete.side_effect = Exception("Delete Error")
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "demo.services.dataset.Dataset.one_by_id", return_value=mock_dataset
            ), patch("demo.services.dataset.get_tenant_id", return_value=None):
                service = DatasetService()
                with pytest.raises(Exception, match="Delete Error"):
                    await service.delete_dataset("test-dataset-id")

        mock_session.rollback.assert_called_once()
