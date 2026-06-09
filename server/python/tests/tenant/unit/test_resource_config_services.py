"""
资源配置服务单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from framework.common.exceptions import ConflictError
from tenant.services.database_config_service import DatabaseConfigService
from tenant.services.storage_config_service import StorageConfigService
from tenant.services.cache_config_service import CacheConfigService
from tenant.services.queue_config_service import QueueConfigService
from tenant.services.pubsub_config_service import PubSubConfigService


class TestDatabaseConfigService:
    """数据库配置服务测试"""

    @pytest.mark.asyncio
    async def test_list_configs_with_keyword(self):
        """带关键词查询配置列表"""
        mock_config = MagicMock()
        mock_config.id = "config-1"
        mock_config.name = "测试数据库"
        mock_config.type = "postgresql"
        mock_config.host = "localhost"
        mock_config.port = 5432
        mock_config.database = "test_db"
        mock_config.username = "admin"
        mock_config.password = "encrypted:password"
        mock_config.created_at = datetime.now()
        mock_config.updated_at = datetime.now()

        with patch("tenant.services.base_resource_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            count_result = MagicMock()
            count_result.scalar.return_value = 1

            list_result = MagicMock()
            list_result.scalars.return_value.all.return_value = [mock_config]

            mock_ctx.execute.side_effect = [count_result, list_result]

            items, total = await DatabaseConfigService.list_configs(
                page=1, page_size=20, keyword="测试"
            )

        assert len(items) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_by_id_returns_config(self):
        """根据 ID 获取配置"""
        mock_config = MagicMock()
        mock_config.id = "config-1"

        with patch("tenant.services.base_resource_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_config
            mock_ctx.execute.return_value = result

            config = await DatabaseConfigService.get_by_id("config-1")

        assert config is mock_config

    @pytest.mark.asyncio
    async def test_create_encrypts_password(self):
        """创建时加密密码"""
        with patch("tenant.services.base_resource_service.encrypt_password") as mock_encrypt, \
             patch("tenant.services.base_resource_service.async_session") as mock_session:

            mock_encrypt.return_value = "encrypted_password"

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.add = MagicMock()
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            await DatabaseConfigService.create(
                name="测试数据库",
                type="postgresql",
                host="localhost",
                port=5432,
                database="test_db",
                username="admin",
                password="plain_password",
            )

        mock_encrypt.assert_called_once_with("plain_password")
        mock_ctx.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_encrypts_password(self):
        """更新时加密密码"""
        mock_config = MagicMock()
        mock_config.id = "config-1"

        with patch("tenant.services.base_resource_service.encrypt_password") as mock_encrypt, \
             patch("tenant.services.base_resource_service.async_session") as mock_session:

            mock_encrypt.return_value = "encrypted_password"

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_config
            mock_ctx.execute.return_value = result
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            config = await DatabaseConfigService.update(
                "config-1", password="new_password"
            )

        mock_encrypt.assert_called_once_with("new_password")
        assert config is mock_config

    @pytest.mark.asyncio
    async def test_delete_returns_true_on_success(self):
        """删除成功返回 True"""
        with patch("tenant.services.base_resource_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            # 第一次调用：引用检查返回 0
            ref_result = MagicMock()
            ref_result.scalar.return_value = 0

            # 第二次调用：删除结果 rowcount = 1
            delete_result = MagicMock()
            delete_result.rowcount = 1

            mock_ctx.execute.side_effect = [ref_result, delete_result]
            mock_ctx.commit = AsyncMock()

            success = await DatabaseConfigService.delete("config-1")

        assert success is True

    @pytest.mark.asyncio
    async def test_test_connection_config_not_found(self):
        """配置不存在时测试连接返回失败"""
        with patch.object(DatabaseConfigService, "get_by_id") as mock_get:
            mock_get.return_value = None

            success, message, latency = await DatabaseConfigService.test_connection(
                "nonexistent"
            )

        assert success is False
        assert "不存在" in message
        assert latency is None

    def test_build_response_masks_password(self):
        """响应脱敏密码"""
        from unittest.mock import create_autospec

        mock_config = MagicMock()
        # 手动模拟 Column 和 Table 结构
        column_id = type("Column", (), {"name": "id"})
        column_name = type("Column", (), {"name": "name"})
        column_pass = type("Column", (), {"name": "password"})
        table = type("Table", (), {"columns": [column_id, column_name, column_pass]})
        mock_config.configure_mock(
            **{
                "__table__": table,
                "id": "config-1",
                "name": "测试",
                "password": "encrypted:password",
            }
        )

        with patch("tenant.services.base_resource_service.mask_password") as mock_mask:
            mock_mask.return_value = "******"

            result = DatabaseConfigService.build_response(mock_config)

        assert result["password"] == "******"


class TestStorageConfigService:
    """存储配置服务测试"""

    @pytest.mark.asyncio
    async def test_create_encrypts_secret_key(self):
        """创建时加密密钥"""
        with patch("tenant.services.base_resource_service.encrypt_password") as mock_encrypt, \
             patch("tenant.services.base_resource_service.async_session") as mock_session:

            mock_encrypt.return_value = "encrypted_secret"

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.add = MagicMock()
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            await StorageConfigService.create(
                name="测试存储",
                type="minio",
                bucket="test-bucket",
                endpoint="http://localhost:9000",
                access_key="access",
                secret_key="plain_secret",
            )

        mock_encrypt.assert_called_once_with("plain_secret")


class TestCacheConfigService:
    """缓存配置服务测试"""

    @pytest.mark.asyncio
    async def test_test_connection_config_not_found(self):
        """配置不存在时测试连接返回失败"""
        with patch.object(CacheConfigService, "get_by_id") as mock_get:
            mock_get.return_value = None

            success, message, latency = await CacheConfigService.test_connection(
                "nonexistent"
            )

        assert success is False
        assert "不存在" in message

    @pytest.mark.asyncio
    async def test_create_encrypts_password(self):
        """创建时加密密码"""
        with patch("tenant.services.base_resource_service.encrypt_password") as mock_encrypt, \
             patch("tenant.services.base_resource_service.async_session") as mock_session:

            mock_encrypt.return_value = "encrypted_password"

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.add = MagicMock()
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            await CacheConfigService.create(
                name="测试缓存",
                host="localhost",
                port=6379,
                password="plain_password",
                db=0,
            )

        mock_encrypt.assert_called_once_with("plain_password")


class TestQueueConfigService:
    """队列配置服务测试"""

    @pytest.mark.asyncio
    async def test_test_connection_unsupported_type(self):
        """不支持的类型返回格式校验成功"""
        mock_config = MagicMock()
        mock_config.id = "config-1"
        mock_config.name = "测试队列"
        mock_config.type = "unsupported"
        mock_config.host = "localhost"
        mock_config.port = 5672
        mock_config.username = None
        mock_config.password = None
        mock_config.vhost = None

        with patch.object(QueueConfigService, "get_by_id") as mock_get:
            mock_get.return_value = mock_config

            success, message, latency = await QueueConfigService.test_connection(
                "config-1"
            )

        assert success is True
        assert "格式校验" in message


class TestPubSubConfigService:
    """发布订阅配置服务测试"""

    @pytest.mark.asyncio
    async def test_test_connection_unsupported_type(self):
        """不支持的类型返回格式校验成功"""
        mock_config = MagicMock()
        mock_config.id = "config-1"
        mock_config.name = "测试发布订阅"
        mock_config.type = "unsupported"
        mock_config.host = "localhost"
        mock_config.port = 9092
        mock_config.username = None
        mock_config.password = None

        with patch.object(PubSubConfigService, "get_by_id") as mock_get:
            mock_get.return_value = mock_config

            success, message, latency = await PubSubConfigService.test_connection(
                "config-1"
            )

        assert success is True
        assert "格式校验" in message

    @pytest.mark.asyncio
    async def test_create_encrypts_password(self):
        """创建时加密密码"""
        with patch("tenant.services.base_resource_service.encrypt_password") as mock_encrypt, \
             patch("tenant.services.base_resource_service.async_session") as mock_session:

            mock_encrypt.return_value = "encrypted_password"

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.add = MagicMock()
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            await PubSubConfigService.create(
                name="测试发布订阅",
                type="redis",
                host="localhost",
                port=6379,
                username="admin",
                password="plain_password",
            )

        mock_encrypt.assert_called_once_with("plain_password")


class TestDeleteProtection:
    """删除保护测试"""

    @pytest.mark.asyncio
    async def test_delete_database_config_with_tenant_reference_raises_conflict(self):
        """数据库配置被租户引用时删除抛出 ConflictError"""
        with patch("tenant.services.base_resource_service.async_session") as mock_session:
            # 模拟引用检查查询
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            ref_result = MagicMock()
            ref_result.scalar.return_value = 3  # 3 个租户引用
            mock_ctx.execute.return_value = ref_result

            with pytest.raises(ConflictError) as exc_info:
                await DatabaseConfigService.delete("config-1")

            assert "3 个租户引用" in str(exc_info.value.message)
            assert mock_ctx.commit.called is False  # 不应执行删除

    @pytest.mark.asyncio
    async def test_delete_storage_config_with_tenant_reference_raises_conflict(self):
        """存储配置被租户引用时删除抛出 ConflictError"""
        with patch("tenant.services.base_resource_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            ref_result = MagicMock()
            ref_result.scalar.return_value = 1  # 1 个租户引用
            mock_ctx.execute.return_value = ref_result

            with pytest.raises(ConflictError) as exc_info:
                await StorageConfigService.delete("config-1")

            assert "1 个租户引用" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_delete_cache_config_with_tenant_reference_raises_conflict(self):
        """缓存配置被租户引用时删除抛出 ConflictError"""
        with patch("tenant.services.base_resource_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            ref_result = MagicMock()
            ref_result.scalar.return_value = 2
            mock_ctx.execute.return_value = ref_result

            with pytest.raises(ConflictError) as exc_info:
                await CacheConfigService.delete("config-1")

            assert "2 个租户引用" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_delete_queue_config_with_tenant_reference_raises_conflict(self):
        """队列配置被租户引用时删除抛出 ConflictError"""
        with patch("tenant.services.base_resource_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            ref_result = MagicMock()
            ref_result.scalar.return_value = 5
            mock_ctx.execute.return_value = ref_result

            with pytest.raises(ConflictError) as exc_info:
                await QueueConfigService.delete("config-1")

            assert "5 个租户引用" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_delete_pubsub_config_with_tenant_reference_raises_conflict(self):
        """发布订阅配置被租户引用时删除抛出 ConflictError"""
        with patch("tenant.services.base_resource_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            ref_result = MagicMock()
            ref_result.scalar.return_value = 1
            mock_ctx.execute.return_value = ref_result

            with pytest.raises(ConflictError) as exc_info:
                await PubSubConfigService.delete("config-1")

            assert "1 个租户引用" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_delete_config_without_reference_succeeds(self):
        """配置无引用时删除成功"""
        with patch("tenant.services.base_resource_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            # 第一次调用返回引用计数 0
            ref_result = MagicMock()
            ref_result.scalar.return_value = 0

            # 第二次调用返回删除结果
            delete_result = MagicMock()
            delete_result.rowcount = 1

            mock_ctx.execute.side_effect = [ref_result, delete_result]
            mock_ctx.commit = AsyncMock()

            success = await DatabaseConfigService.delete("config-1")

            assert success is True
            assert mock_ctx.commit.called is True

    @pytest.mark.asyncio
    async def test_delete_config_not_found_returns_false(self):
        """删除不存在的配置返回 False"""
        with patch("tenant.services.base_resource_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            # 引用计数 0
            ref_result = MagicMock()
            ref_result.scalar.return_value = 0

            # 删除结果 rowcount = 0
            delete_result = MagicMock()
            delete_result.rowcount = 0

            mock_ctx.execute.side_effect = [ref_result, delete_result]
            mock_ctx.commit = AsyncMock()

            success = await DatabaseConfigService.delete("nonexistent")

            assert success is False
