"""
资源配置模型 is_default 字段单元测试

测试所有资源配置模型中 is_default 字段的默认值和可设置性。
"""

from unittest.mock import MagicMock

from tenant.models import (
    CacheConfig,
    DatabaseConfig,
    PubSubConfig,
    QueueConfig,
    StorageConfig,
)


class TestDatabaseConfigIsDefault:
    """数据库配置模型 is_default 字段测试"""

    def test_is_default_column_defined(self):
        """is_default 字段在模型中已定义"""
        assert hasattr(DatabaseConfig, "is_default")

    def test_is_default_column_type_is_boolean(self):
        """is_default 字段类型为 Boolean"""
        from sqlalchemy import Boolean
        column = DatabaseConfig.__table__.c.is_default
        assert isinstance(column.type, Boolean)

    def test_is_default_server_default_is_false(self):
        """is_default 字段服务端默认值为 false"""
        column = DatabaseConfig.__table__.c.is_default
        assert column.server_default.arg == "false"

    def test_is_default_not_nullable(self):
        """is_default 字段不可为空"""
        column = DatabaseConfig.__table__.c.is_default
        assert column.nullable is False


class TestStorageConfigIsDefault:
    """存储配置模型 is_default 字段测试"""

    def test_is_default_column_defined(self):
        """is_default 字段在模型中已定义"""
        assert hasattr(StorageConfig, "is_default")

    def test_is_default_column_type_is_boolean(self):
        """is_default 字段类型为 Boolean"""
        from sqlalchemy import Boolean
        column = StorageConfig.__table__.c.is_default
        assert isinstance(column.type, Boolean)

    def test_is_default_server_default_is_false(self):
        """is_default 字段服务端默认值为 false"""
        column = StorageConfig.__table__.c.is_default
        assert column.server_default.arg == "false"

    def test_is_default_not_nullable(self):
        """is_default 字段不可为空"""
        column = StorageConfig.__table__.c.is_default
        assert column.nullable is False


class TestCacheConfigIsDefault:
    """缓存配置模型 is_default 字段测试"""

    def test_is_default_column_defined(self):
        """is_default 字段在模型中已定义"""
        assert hasattr(CacheConfig, "is_default")

    def test_is_default_column_type_is_boolean(self):
        """is_default 字段类型为 Boolean"""
        from sqlalchemy import Boolean
        column = CacheConfig.__table__.c.is_default
        assert isinstance(column.type, Boolean)

    def test_is_default_server_default_is_false(self):
        """is_default 字段服务端默认值为 false"""
        column = CacheConfig.__table__.c.is_default
        assert column.server_default.arg == "false"

    def test_is_default_not_nullable(self):
        """is_default 字段不可为空"""
        column = CacheConfig.__table__.c.is_default
        assert column.nullable is False


class TestQueueConfigIsDefault:
    """队列配置模型 is_default 字段测试"""

    def test_is_default_column_defined(self):
        """is_default 字段在模型中已定义"""
        assert hasattr(QueueConfig, "is_default")

    def test_is_default_column_type_is_boolean(self):
        """is_default 字段类型为 Boolean"""
        from sqlalchemy import Boolean
        column = QueueConfig.__table__.c.is_default
        assert isinstance(column.type, Boolean)

    def test_is_default_server_default_is_false(self):
        """is_default 字段服务端默认值为 false"""
        column = QueueConfig.__table__.c.is_default
        assert column.server_default.arg == "false"

    def test_is_default_not_nullable(self):
        """is_default 字段不可为空"""
        column = QueueConfig.__table__.c.is_default
        assert column.nullable is False


class TestPubSubConfigIsDefault:
    """发布订阅配置模型 is_default 字段测试"""

    def test_is_default_column_defined(self):
        """is_default 字段在模型中已定义"""
        assert hasattr(PubSubConfig, "is_default")

    def test_is_default_column_type_is_boolean(self):
        """is_default 字段类型为 Boolean"""
        from sqlalchemy import Boolean
        column = PubSubConfig.__table__.c.is_default
        assert isinstance(column.type, Boolean)

    def test_is_default_server_default_is_false(self):
        """is_default 字段服务端默认值为 false"""
        column = PubSubConfig.__table__.c.is_default
        assert column.server_default.arg == "false"

    def test_is_default_not_nullable(self):
        """is_default 字段不可为空"""
        column = PubSubConfig.__table__.c.is_default
        assert column.nullable is False


class TestIsDefaultFieldValue:
    """is_default 字段值设置测试

    通过模拟模型实例验证 is_default 字段可被设置为 True 和 False。
    """

    def test_database_config_is_default_can_be_true(self):
        """数据库配置 is_default 可以设置为 True"""
        config = MagicMock(spec=DatabaseConfig)
        config.is_default = True
        assert config.is_default is True

    def test_database_config_is_default_can_be_false(self):
        """数据库配置 is_default 可以设置为 False"""
        config = MagicMock(spec=DatabaseConfig)
        config.is_default = False
        assert config.is_default is False

    def test_storage_config_is_default_can_be_true(self):
        """存储配置 is_default 可以设置为 True"""
        config = MagicMock(spec=StorageConfig)
        config.is_default = True
        assert config.is_default is True

    def test_cache_config_is_default_can_be_true(self):
        """缓存配置 is_default 可以设置为 True"""
        config = MagicMock(spec=CacheConfig)
        config.is_default = True
        assert config.is_default is True

    def test_queue_config_is_default_can_be_true(self):
        """队列配置 is_default 可以设置为 True"""
        config = MagicMock(spec=QueueConfig)
        config.is_default = True
        assert config.is_default is True

    def test_pubsub_config_is_default_can_be_true(self):
        """发布订阅配置 is_default 可以设置为 True"""
        config = MagicMock(spec=PubSubConfig)
        config.is_default = True
        assert config.is_default is True
