"""
资源配置种子脚本测试

测试从配置创建默认配置、幂等性和 is_default 正确设置。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from tenant.migrations.seeds.resource_config_seed import (
    DEFAULT_CONFIG_NAME,
    _parse_database_url,
    _create_database_config,
    _create_cache_config,
    _create_storage_config,
    _create_queue_config,
    _create_pubsub_config,
    run,
)
from tenant.models import (
    DatabaseConfig,
    CacheConfig,
    StorageConfig,
    QueueConfig,
    PubSubConfig,
)


class TestParseDatabaseUrl:
    """数据库 URL 解析测试"""

    def test_parse_postgresql_url(self):
        """解析 PostgreSQL 连接字符串"""
        url = "postgresql+asyncpg://user:password@localhost:5432/ai_platform"
        result = _parse_database_url(url)
        assert result["type"] == "postgresql"
        assert result["host"] == "localhost"
        assert result["port"] == 5432
        assert result["database"] == "ai_platform"
        assert result["username"] == "user"
        assert result["password"] == "password"

    def test_parse_mysql_url(self):
        """解析 MySQL 连接字符串"""
        url = "mysql+aiomysql://root:pass@db.example.com:3306/mydb"
        result = _parse_database_url(url)
        assert result["type"] == "mysql"
        assert result["host"] == "db.example.com"
        assert result["port"] == 3306
        assert result["database"] == "mydb"

    def test_parse_url_without_driver(self):
        """解析不带驱动前缀的 URL"""
        url = "postgresql://user:pass@localhost:5432/testdb"
        result = _parse_database_url(url)
        assert result["type"] == "postgresql"

    def test_default_config_name_is_default(self):
        """默认配置名称为 'default'"""
        assert DEFAULT_CONFIG_NAME == "default"


class TestCreateDatabaseConfig:
    """创建默认数据库配置测试"""

    @pytest.mark.asyncio
    async def test_creates_config_with_is_default_true(self):
        """创建的配置 is_default 设置为 True"""
        mock_session = AsyncMock()
        # 模拟配置不存在
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result_mock

        mock_settings = MagicMock()
        mock_settings.sqlalchemy.url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"

        with patch("framework.utils.crypto.encrypt", return_value="encrypted_pass"):
            result = await _create_database_config(mock_session, mock_settings)

        assert result is True
        # 验证 session.add 被调用，创建的对象 is_default=True
        mock_session.add.assert_called_once()
        added_obj = mock_session.add.call_args[0][0]
        assert isinstance(added_obj, DatabaseConfig)
        assert added_obj.is_default is True

    @pytest.mark.asyncio
    async def test_skips_if_already_exists(self):
        """配置已存在时跳过创建（幂等性）"""
        mock_session = AsyncMock()
        existing_config = MagicMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_config
        mock_session.execute.return_value = result_mock

        mock_settings = MagicMock()
        mock_settings.sqlalchemy.url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"

        result = await _create_database_config(mock_session, mock_settings)

        assert result is False
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_if_url_not_configured(self):
        """数据库 URL 未配置时跳过创建"""
        mock_session = AsyncMock()

        mock_settings = MagicMock()
        mock_settings.sqlalchemy.url = None

        result = await _create_database_config(mock_session, mock_settings)

        assert result is False
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_config_name_is_default(self):
        """创建的配置名称为 'default'"""
        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result_mock

        mock_settings = MagicMock()
        mock_settings.sqlalchemy.url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"

        with patch("framework.utils.crypto.encrypt", return_value="encrypted_pass"):
            await _create_database_config(mock_session, mock_settings)

        added_obj = mock_session.add.call_args[0][0]
        assert added_obj.name == DEFAULT_CONFIG_NAME


class TestCreateCacheConfig:
    """创建默认缓存配置测试"""

    @pytest.mark.asyncio
    async def test_creates_config_with_is_default_true(self):
        """创建的配置 is_default 设置为 True"""
        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result_mock

        mock_settings = MagicMock()
        mock_settings.redis.single.host = "localhost"
        mock_settings.redis.single.port = 6379
        mock_settings.redis.single.password = "redis_pass"
        mock_settings.redis.single.db = 0

        with patch("framework.utils.crypto.encrypt", return_value="encrypted_pass"):
            await _create_cache_config(mock_session, mock_settings)

        added_obj = mock_session.add.call_args[0][0]
        assert isinstance(added_obj, CacheConfig)
        assert added_obj.is_default is True

    @pytest.mark.asyncio
    async def test_skips_if_already_exists(self):
        """配置已存在时跳过创建（幂等性）"""
        mock_session = AsyncMock()
        existing_config = MagicMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_config
        mock_session.execute.return_value = result_mock

        mock_settings = MagicMock()
        result = await _create_cache_config(mock_session, mock_settings)

        assert result is False
        mock_session.add.assert_not_called()


class TestCreateStorageConfig:
    """创建默认存储配置测试"""

    @pytest.mark.asyncio
    async def test_creates_config_with_is_default_true(self):
        """创建的配置 is_default 设置为 True"""
        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result_mock

        mock_settings = MagicMock()
        mock_settings.oss.default_type = "minio"
        mock_settings.oss.bucket = "test-bucket"
        mock_settings.oss.minio.endpoint = "http://localhost:9000"
        mock_settings.oss.minio.access_key = "access"
        mock_settings.oss.minio.secret_key = "secret"

        with patch("framework.utils.crypto.encrypt", return_value="encrypted_secret"):
            await _create_storage_config(mock_session, mock_settings)

        added_obj = mock_session.add.call_args[0][0]
        assert isinstance(added_obj, StorageConfig)
        assert added_obj.is_default is True

    @pytest.mark.asyncio
    async def test_skips_if_already_exists(self):
        """配置已存在时跳过创建（幂等性）"""
        mock_session = AsyncMock()
        existing_config = MagicMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_config
        mock_session.execute.return_value = result_mock

        mock_settings = MagicMock()
        result = await _create_storage_config(mock_session, mock_settings)

        assert result is False
        mock_session.add.assert_not_called()


class TestCreateQueueConfig:
    """创建默认队列配置测试"""

    @pytest.mark.asyncio
    async def test_creates_config_with_is_default_true(self):
        """创建的配置 is_default 设置为 True"""
        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result_mock

        mock_settings = MagicMock()
        mock_settings.redis.single.host = "localhost"
        mock_settings.redis.single.port = 6379
        mock_settings.redis.single.password = "redis_pass"
        mock_settings.messaging.queue.use = "redis"

        with patch("framework.utils.crypto.encrypt", return_value="encrypted_pass"):
            await _create_queue_config(mock_session, mock_settings)

        added_obj = mock_session.add.call_args[0][0]
        assert isinstance(added_obj, QueueConfig)
        assert added_obj.is_default is True


class TestCreatePubSubConfig:
    """创建默认发布订阅配置测试"""

    @pytest.mark.asyncio
    async def test_creates_config_with_is_default_true(self):
        """创建的配置 is_default 设置为 True"""
        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result_mock

        mock_settings = MagicMock()
        mock_settings.redis.single.host = "localhost"
        mock_settings.redis.single.port = 6379
        mock_settings.redis.single.password = "redis_pass"
        mock_settings.messaging.pubsub.use = "redis"

        with patch("framework.utils.crypto.encrypt", return_value="encrypted_pass"):
            await _create_pubsub_config(mock_session, mock_settings)

        added_obj = mock_session.add.call_args[0][0]
        assert isinstance(added_obj, PubSubConfig)
        assert added_obj.is_default is True


class TestSeedRunIdempotency:
    """种子脚本幂等性测试"""

    @pytest.mark.asyncio
    async def test_dry_run_returns_count(self):
        """dry_run 模式返回预估数量"""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("framework.configs.get_settings") as mock_get_settings, \
             patch("framework.database.core.engine.get_session", return_value=mock_session):
            mock_get_settings.return_value = MagicMock()

            result = await run(dry_run=True)

            assert result == 5

    @pytest.mark.asyncio
    async def test_run_returns_zero_when_all_exist(self):
        """所有默认配置已存在时返回 0"""
        mock_session = AsyncMock()
        # 模拟所有配置已存在
        existing = MagicMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing
        mock_session.execute.return_value = result_mock
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.commit = AsyncMock()

        with patch("framework.configs.get_settings") as mock_get_settings, \
             patch("framework.database.core.engine.get_session", return_value=mock_session):
            mock_get_settings.return_value = MagicMock()

            result = await run(dry_run=False)

            assert result == 0
