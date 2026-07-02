"""
is_default 唯一性控制服务层测试

测试创建和更新默认配置时清除其他默认标记，以及 get_default_config 方法。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tenant.services.cache_config_service import CacheConfigService
from tenant.services.database_config_service import DatabaseConfigService
from tenant.services.pubsub_config_service import PubSubConfigService
from tenant.services.queue_config_service import QueueConfigService
from tenant.services.storage_config_service import StorageConfigService


class TestClearExistingDefault:
    """_clear_existing_default 方法测试"""

    @pytest.mark.asyncio
    async def test_clear_existing_default_executes_update(self, mock_session):
        """清除默认标记时执行 UPDATE 语句"""
        await DatabaseConfigService._clear_existing_default(mock_session)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_existing_default_for_all_services(self, mock_session):
        """所有资源配置服务都支持清除默认标记"""
        services = [
            DatabaseConfigService,
            StorageConfigService,
            CacheConfigService,
            QueueConfigService,
            PubSubConfigService,
        ]

        for service in services:
            await service._clear_existing_default(mock_session)
            mock_session.execute.assert_called_once()
            mock_session.execute.reset_mock()


class TestCreateDefaultConfig:
    """创建默认配置时的唯一性控制测试"""

    @pytest.mark.asyncio
    async def test_create_with_is_default_clears_others(self, mock_session):
        """创建 is_default=True 的配置时清除其他默认标记"""
        with patch("tenant.services.base_resource_service.encrypt_password", side_effect=lambda x: f"enc_{x}"), \
             patch.object(DatabaseConfigService, "_clear_existing_default", new_callable=AsyncMock) as mock_clear:

            await DatabaseConfigService.create(
                session=session,
                name="新默认数据库",
                type="postgresql",
                host="localhost",
                port=5432,
                database="test_db",
                username="admin",
                password="plain_password",
                is_default=True,
            )

        mock_clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_without_is_default_does_not_clear_others(self, mock_session):
        """创建 is_default=False 的配置时不清除其他默认标记"""
        with patch("tenant.services.base_resource_service.encrypt_password", side_effect=lambda x: f"enc_{x}"), \
             patch.object(DatabaseConfigService, "_clear_existing_default", new_callable=AsyncMock) as mock_clear:

            await DatabaseConfigService.create(
                session=session,
                name="非默认数据库",
                type="postgresql",
                host="localhost",
                port=5432,
                database="test_db",
                username="admin",
                password="plain_password",
                is_default=False,
            )

        mock_clear.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_default_without_is_default_param_does_not_clear(self, mock_session):
        """创建时不传 is_default 参数（默认为 False）不清除其他默认标记"""
        with patch("tenant.services.base_resource_service.encrypt_password", side_effect=lambda x: f"enc_{x}"), \
             patch.object(DatabaseConfigService, "_clear_existing_default", new_callable=AsyncMock) as mock_clear:

            await DatabaseConfigService.create(
                session=session,
                name="普通数据库",
                type="postgresql",
                host="localhost",
                port=5432,
                database="test_db",
                username="admin",
                password="plain_password",
            )

        mock_clear.assert_not_called()


class TestUpdateDefaultConfig:
    """更新配置为默认时的唯一性控制测试"""

    @pytest.mark.asyncio
    async def test_update_to_default_clears_others(self, mock_session):
        """将配置更新为 is_default=True 时清除其他默认标记"""
        mock_config = MagicMock()
        mock_config.id = "config-1"

        with patch.object(DatabaseConfigService, "_clear_existing_default", new_callable=AsyncMock) as mock_clear:

            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = mock_config
            mock_session.execute.return_value = result_mock

            await DatabaseConfigService.update(
                mock_session,
                "config-1",
                is_default=True,
            )

        mock_clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_to_non_default_does_not_clear_others(self, mock_session):
        """将配置更新为 is_default=False 时不清除其他默认标记"""
        mock_config = MagicMock()
        mock_config.id = "config-1"

        with patch.object(DatabaseConfigService, "_clear_existing_default", new_callable=AsyncMock) as mock_clear:

            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = mock_config
            mock_session.execute.return_value = result_mock

            await DatabaseConfigService.update(
                mock_session,
                "config-1",
                is_default=False,
            )

        mock_clear.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_other_field_does_not_clear_others(self, mock_session):
        """更新其他字段（不涉及 is_default）时不清除默认标记"""
        mock_config = MagicMock()
        mock_config.id = "config-1"

        with patch.object(DatabaseConfigService, "_clear_existing_default", new_callable=AsyncMock) as mock_clear, \
             patch("tenant.services.base_resource_service.encrypt_password", side_effect=lambda x: f"enc_{x}"):

            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = mock_config
            mock_session.execute.return_value = result_mock

            await DatabaseConfigService.update(
                mock_session,
                "config-1",
                name="更新后的名称",
            )

        mock_clear.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(self, mock_session):
        """更新不存在的配置返回 None"""
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result_mock

        result = await DatabaseConfigService.update(
            mock_session,
            "nonexistent",
            is_default=True,
        )

        assert result is None


class TestGetDefaultConfig:
    """get_default_config 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_default_config(self, mock_session):
        """查询到默认配置时返回配置实例"""
        mock_config = MagicMock()
        mock_config.is_default = True

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_config
        mock_session.execute.return_value = result_mock

        config = await DatabaseConfigService.get_default_config(session=session)

        assert config is mock_config
        assert config.is_default is True

    @pytest.mark.asyncio
    async def test_returns_none_when_no_default(self, mock_session):
        """没有默认配置时返回 None"""
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result_mock

        config = await DatabaseConfigService.get_default_config(session=session)

        assert config is None

    @pytest.mark.asyncio
    async def test_all_services_have_get_default_config(self):
        """所有资源配置服务都支持 get_default_config 方法"""
        services = [
            DatabaseConfigService,
            StorageConfigService,
            CacheConfigService,
            QueueConfigService,
            PubSubConfigService,
        ]

        for service in services:
            assert hasattr(service, "get_default_config")
            assert callable(service.get_default_config)


class TestListConfigsDefaultOrdering:
    """配置列表默认排序测试"""

    @pytest.mark.asyncio
    async def test_list_configs_orders_default_first(self, mock_session):
        """配置列表中默认配置排在最前"""
        mock_default = MagicMock()
        mock_default.is_default = True
        mock_default.name = "默认配置"

        mock_normal = MagicMock()
        mock_normal.is_default = False
        mock_normal.name = "普通配置"

        count_result = MagicMock()
        count_result.scalar.return_value = 2

        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [mock_default, mock_normal]

        mock_session.execute.side_effect = [count_result, list_result]

        items, total = await DatabaseConfigService.list_configs(session=session)

        assert total == 2
        assert items[0].is_default is True


class TestDeleteDefaultConfig:
    """删除默认配置时的警告测试"""

    @pytest.mark.asyncio
    async def test_delete_default_config_raises_error(self, mock_session):
        """删除默认配置时抛出 ConflictError"""
        from framework.common.exceptions import ConflictError

        mock_config = MagicMock()
        mock_config.id = "test-id"
        mock_config.is_default = True

        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = mock_config
        mock_session.execute.return_value = query_result

        with pytest.raises(ConflictError) as exc_info:
            await DatabaseConfigService.delete(mock_session, "test-id")

        assert "默认配置" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_normal_config_succeeds(self, mock_session):
        """删除非默认配置成功"""
        mock_config = MagicMock()
        mock_config.id = "test-id"
        mock_config.is_default = False

        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = mock_config

        count_result = MagicMock()
        count_result.scalar.return_value = 0

        delete_result = MagicMock()
        delete_result.rowcount = 1

        # execute 调用顺序：查询配置 -> 检查引用计数 -> 执行删除
        mock_session.execute.side_effect = [query_result, count_result, delete_result]

        result = await DatabaseConfigService.delete(mock_session, "test-id")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_config_referenced_by_tenant_raises_error(self, mock_session):
        """删除被租户引用的配置时抛出 ConflictError"""
        from framework.common.exceptions import ConflictError

        mock_config = MagicMock()
        mock_config.id = "test-id"
        mock_config.is_default = False

        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = mock_config

        count_result = MagicMock()
        count_result.scalar.return_value = 3

        mock_session.execute.side_effect = [query_result, count_result]

        with pytest.raises(ConflictError) as exc_info:
            await DatabaseConfigService.delete(mock_session, "test-id")

        assert "租户使用" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_config_returns_false(self, mock_session):
        """删除不存在的配置返回 False"""
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = query_result

        result = await DatabaseConfigService.delete(mock_session, "nonexistent-id")

        assert result is False
