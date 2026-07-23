"""
资源配置服务单元测试
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework.common.exceptions import ConflictError
from tenant.services.resource import CacheConfigService
from tenant.services.resource import DatabaseConfigService
from tenant.services.resource import PubSubConfigService
from tenant.services.resource import QueueConfigService
from tenant.services.resource import StorageConfigService


class TestDatabaseConfigService:
    """数据库配置服务测试"""

    @pytest.mark.asyncio
    async def test_list_configs_with_keyword(self, mock_session):
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

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [mock_config]

        mock_session.execute.side_effect = [count_result, list_result]

        items, total = await DatabaseConfigService.list_configs(
            mock_session, page=1, page_size=20, keyword="测试"
        )

        assert len(items) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_by_id_returns_config(self, mock_session):
        """根据 ID 获取配置"""
        mock_config = MagicMock()
        mock_config.id = "config-1"

        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_config
        mock_session.execute.return_value = result

        config = await DatabaseConfigService.get_by_id(mock_session, "config-1")

        assert config is mock_config

    @pytest.mark.asyncio
    async def test_create_encrypts_password(self, mock_session):
        """创建时加密密码"""
        with patch("tenant.services.base_resource_service.encrypt_password") as mock_encrypt:

            mock_encrypt.return_value = "encrypted_password"

            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            await DatabaseConfigService.create(
                mock_session,
                name="测试数据库",
                type="postgresql",
                host="localhost",
                port=5432,
                database="test_db",
                username="admin",
                password="plain_password",
            )

        mock_encrypt.assert_called_once_with("plain_password")
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_encrypts_password(self, mock_session):
        """更新时加密密码"""
        mock_config = MagicMock()
        mock_config.id = "config-1"

        with patch("tenant.services.base_resource_service.encrypt_password") as mock_encrypt:

            mock_encrypt.return_value = "encrypted_password"

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_config
            mock_session.execute.return_value = result
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            config = await DatabaseConfigService.update(
                mock_session, "config-1", password="new_password"
            )

        mock_encrypt.assert_called_once_with("new_password")
        assert config is mock_config

    @pytest.mark.asyncio
    async def test_delete_returns_true_on_success(self, mock_session):
        """删除成功返回 True"""
        # 模拟配置查询返回非默认配置
        mock_config = MagicMock()
        mock_config.id = "config-1"
        mock_config.is_default = False

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config

        # 第一次调用：引用检查返回 0
        ref_result = MagicMock()
        ref_result.scalar.return_value = 0

        # 第二次调用：删除结果 rowcount = 1
        delete_result = MagicMock()
        delete_result.rowcount = 1

        mock_session.execute.side_effect = [config_result, ref_result, delete_result]
        mock_session.flush = AsyncMock()

        success = await DatabaseConfigService.delete(mock_session, "config-1")

        assert success is True

    @pytest.mark.asyncio
    async def test_test_connection_config_not_found(self, mock_session):
        """配置不存在时测试连接返回失败"""
        with patch.object(DatabaseConfigService, "get_by_id") as mock_get:
            mock_get.return_value = None

            success, message, latency = await DatabaseConfigService.test_connection(
                mock_session, "nonexistent"
            )

        assert success is False
        assert "不存在" in message
        assert latency is None

    def test_build_response_masks_password(self):
        """响应脱敏密码"""

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
    async def test_create_encrypts_secret_key(self, mock_session):
        """创建时加密密钥"""
        with patch("tenant.services.base_resource_service.encrypt_password") as mock_encrypt:

            mock_encrypt.return_value = "encrypted_secret"

            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            await StorageConfigService.create(
                mock_session,
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
    async def test_test_connection_config_not_found(self, mock_session):
        """配置不存在时测试连接返回失败"""
        with patch.object(CacheConfigService, "get_by_id") as mock_get:
            mock_get.return_value = None

            success, message, latency = await CacheConfigService.test_connection(
                mock_session, "nonexistent"
            )

        assert success is False
        assert "不存在" in message

    @pytest.mark.asyncio
    async def test_create_encrypts_password(self, mock_session):
        """创建时加密密码"""
        with patch("tenant.services.base_resource_service.encrypt_password") as mock_encrypt:

            mock_encrypt.return_value = "encrypted_password"

            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            await CacheConfigService.create(
                mock_session,
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
    async def test_test_connection_unsupported_type(self, mock_session):
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
                mock_session, "config-1"
            )

        assert success is True
        assert "格式校验" in message


class TestPubSubConfigService:
    """发布订阅配置服务测试"""

    @pytest.mark.asyncio
    async def test_test_connection_unsupported_type(self, mock_session):
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
                mock_session, "config-1"
            )

        assert success is True
        assert "格式校验" in message

    @pytest.mark.asyncio
    async def test_create_encrypts_password(self, mock_session):
        """创建时加密密码"""
        with patch("tenant.services.base_resource_service.encrypt_password") as mock_encrypt:

            mock_encrypt.return_value = "encrypted_password"

            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            await PubSubConfigService.create(
                mock_session,
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
    async def test_delete_database_config_with_tenant_reference_raises_conflict(self, mock_session):
        """数据库配置被租户引用时删除抛出 ConflictError"""
        # 模拟配置查询返回非默认配置
        mock_config = MagicMock()
        mock_config.id = "config-1"
        mock_config.is_default = False

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config

        # 模拟引用检查查询
        ref_result = MagicMock()
        ref_result.scalar.return_value = 3  # 3 个租户引用

        mock_session.execute.side_effect = [config_result, ref_result]

        with pytest.raises(ConflictError) as exc_info:
            await DatabaseConfigService.delete(mock_session, "config-1")

        assert "被租户使用" in str(exc_info.value.message)
        assert mock_session.commit.called is False  # 不应执行删除

    @pytest.mark.asyncio
    async def test_delete_storage_config_with_tenant_reference_raises_conflict(self, mock_session):
        """存储配置被租户引用时删除抛出 ConflictError"""
        # 模拟配置查询返回非默认配置
        mock_config = MagicMock()
        mock_config.id = "config-1"
        mock_config.is_default = False

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config

        ref_result = MagicMock()
        ref_result.scalar.return_value = 1  # 1 个租户引用

        mock_session.execute.side_effect = [config_result, ref_result]

        with pytest.raises(ConflictError) as exc_info:
            await StorageConfigService.delete(mock_session, "config-1")

        assert "被租户使用" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_delete_cache_config_with_tenant_reference_raises_conflict(self, mock_session):
        """缓存配置被租户引用时删除抛出 ConflictError"""
        # 模拟配置查询返回非默认配置
        mock_config = MagicMock()
        mock_config.id = "config-1"
        mock_config.is_default = False

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config

        ref_result = MagicMock()
        ref_result.scalar.return_value = 2

        mock_session.execute.side_effect = [config_result, ref_result]

        with pytest.raises(ConflictError) as exc_info:
            await CacheConfigService.delete(mock_session, "config-1")

        assert "被租户使用" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_delete_queue_config_with_tenant_reference_raises_conflict(self, mock_session):
        """队列配置被租户引用时删除抛出 ConflictError"""
        # 模拟配置查询返回非默认配置
        mock_config = MagicMock()
        mock_config.id = "config-1"
        mock_config.is_default = False

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config

        ref_result = MagicMock()
        ref_result.scalar.return_value = 5

        mock_session.execute.side_effect = [config_result, ref_result]

        with pytest.raises(ConflictError) as exc_info:
            await QueueConfigService.delete(mock_session, "config-1")

        assert "被租户使用" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_delete_pubsub_config_with_tenant_reference_raises_conflict(self, mock_session):
        """发布订阅配置被租户引用时删除抛出 ConflictError"""
        # 模拟配置查询返回非默认配置
        mock_config = MagicMock()
        mock_config.id = "config-1"
        mock_config.is_default = False

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config

        ref_result = MagicMock()
        ref_result.scalar.return_value = 1

        mock_session.execute.side_effect = [config_result, ref_result]

        with pytest.raises(ConflictError) as exc_info:
            await PubSubConfigService.delete(mock_session, "config-1")

        assert "被租户使用" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_delete_config_without_reference_succeeds(self, mock_session):
        """配置无引用时删除成功"""
        # 模拟配置查询返回非默认配置
        mock_config = MagicMock()
        mock_config.id = "config-1"
        mock_config.is_default = False

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config

        # 第一次调用返回引用计数 0
        ref_result = MagicMock()
        ref_result.scalar.return_value = 0

        # 第二次调用返回删除结果
        delete_result = MagicMock()
        delete_result.rowcount = 1

        mock_session.execute.side_effect = [config_result, ref_result, delete_result]
        mock_session.flush = AsyncMock()

        success = await DatabaseConfigService.delete(mock_session, "config-1")

        assert success is True

    @pytest.mark.asyncio
    async def test_delete_config_not_found_returns_false(self, mock_session):
        """删除不存在的配置返回 False"""
        # 配置查询返回 None
        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = None

        mock_session.execute.return_value = config_result

        success = await DatabaseConfigService.delete(mock_session, "nonexistent")

        assert success is False
