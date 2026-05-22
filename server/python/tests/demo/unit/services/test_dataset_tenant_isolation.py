"""Dataset 租户隔离单元测试"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from demo.schemas.dataset import DatasetCreate, DatasetUpdate
from demo.services.dataset import DatasetService


class TestDatasetTenantIsolation:
    """Dataset 租户隔离单元测试"""

    @pytest.mark.asyncio
    async def test_create_dataset_injects_tenant_id(self):
        """测试创建知识库时自动注入当前租户 ID"""
        # Arrange: 模拟当前租户上下文
        tenant_id = "tenant-123"

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_dataset = MagicMock()
        mock_dataset.id = "dataset-001"
        mock_dataset.name = "测试知识库"
        mock_dataset.tenant_id = tenant_id

        # Act: 创建时应该自动注入 tenant_id
        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("demo.services.dataset.Dataset.create", return_value=mock_dataset) as mock_create:
                with patch("demo.services.dataset.get_tenant_id", return_value=tenant_id):
                    service = DatasetService()
                    data = DatasetCreate(name="测试知识库", description="描述")
                    result = await service.create_dataset(data)

        # Assert: Dataset.create 应该被调用时包含 tenant_id
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1] if mock_create.call_args[1] else mock_create.call_args[0][1]
        assert call_kwargs.get("tenant_id") == tenant_id, "create_dataset 必须自动注入当前租户 ID"
        assert result.tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_list_datasets_filters_by_tenant(self):
        """测试查询知识库时自动按租户过滤"""
        # Arrange: 两个租户各有不同的数据集
        tenant_id = "tenant-A"

        mock_session = AsyncMock()
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_datasets_result = MagicMock()
        mock_dataset = MagicMock()
        mock_dataset.id = "dataset-A"
        mock_dataset.tenant_id = tenant_id
        mock_datasets_result.scalars.return_value.all.return_value = [mock_dataset]

        mock_session.execute.side_effect = [mock_count_result, mock_datasets_result]
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("demo.services.dataset.get_tenant_id", return_value=tenant_id):
                service = DatasetService()
                total, datasets = await service.list_datasets(page=1, page_size=10)

        # Assert: 结果应该只包含当前租户的数据
        assert total == 1
        assert len(datasets) == 1
        assert datasets[0].tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_get_dataset_returns_none_for_other_tenant(self):
        """测试获取其他租户知识库时返回 None"""
        tenant_id = "tenant-A"
        other_tenant_dataset = MagicMock()
        other_tenant_dataset.id = "dataset-B"
        other_tenant_dataset.tenant_id = "tenant-B"

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("demo.services.dataset.Dataset.one_by_id", return_value=other_tenant_dataset):
                with patch("demo.services.dataset.get_tenant_id", return_value=tenant_id):
                    service = DatasetService()
                    result = await service.get_dataset("dataset-B")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_dataset_returns_none_for_other_tenant(self):
        """测试更新其他租户知识库时返回 None"""
        tenant_id = "tenant-A"
        other_tenant_dataset = MagicMock()
        other_tenant_dataset.id = "dataset-B"
        other_tenant_dataset.tenant_id = "tenant-B"
        other_tenant_dataset.update = AsyncMock()

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("demo.services.dataset.Dataset.one_by_id", return_value=other_tenant_dataset):
                with patch("demo.services.dataset.get_tenant_id", return_value=tenant_id):
                    service = DatasetService()
                    result = await service.update_dataset("dataset-B", DatasetUpdate(name="新名称"))

        assert result is None
        other_tenant_dataset.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_dataset_returns_false_for_other_tenant(self):
        """测试删除其他租户知识库时返回 False"""
        tenant_id = "tenant-A"
        other_tenant_dataset = MagicMock()
        other_tenant_dataset.id = "dataset-B"
        other_tenant_dataset.tenant_id = "tenant-B"

        mock_session = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("demo.services.dataset.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("demo.services.dataset.Dataset.one_by_id", return_value=other_tenant_dataset):
                with patch("demo.services.dataset.get_tenant_id", return_value=tenant_id):
                    service = DatasetService()
                    result = await service.delete_dataset("dataset-B")

        assert result is False
        mock_session.delete.assert_not_called()
