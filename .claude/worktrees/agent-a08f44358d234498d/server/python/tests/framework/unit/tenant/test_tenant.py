"""
tenant 模块单元测试
"""

import pytest

from framework.tenant.protocols import (
    TenantDatabaseConfig,
    TenantStorageConfig,
    TenantQueueConfig,
    TenantPubSubConfig,
    TenantInfo,
    TenantProvider,
    register_tenant_provider,
    get_tenant_provider,
)
from framework.tenant.enums import DatabaseType, StorageType, QueueType
from framework.tenant.context import (
    TenantContext,
    SimpleTenant,
    get_current_tenant,
    set_current_tenant,
    get_tenant_id,
)
from framework.tenant.middleware import TenantMiddleware


class TestTenantMiddleware:
    """TenantMiddleware 测试"""

    def test_root_path_skips_tenant_resolution(self):
        """
        场景：访问根路径
        WHEN: 检查是否跳过租户校验
        THEN: 根路径不要求 X-Tenant-Id
        """

        class MockURL:
            path = "/"

        class MockRequest:
            url = MockURL()

        middleware = TenantMiddleware(app=lambda scope, receive, send: None)

        assert middleware._should_skip(MockRequest()) is True


class TestTenantEnums:
    """租户枚举测试"""

    def test_database_type_values(self):
        """
        场景：数据库类型枚举
        WHEN: 访问枚举值
        THEN: 返回正确字符串
        """
        assert DatabaseType.POSTGRESQL.value == "postgresql"
        assert DatabaseType.MYSQL.value == "mysql"
        assert DatabaseType.SQLITE.value == "sqlite"

    def test_storage_type_values(self):
        """
        场景：存储类型枚举
        WHEN: 访问枚举值
        THEN: 返回正确字符串
        """
        assert StorageType.MINIO.value == "minio"
        assert StorageType.ALIYUN.value == "aliyun"
        assert StorageType.TENCENT.value == "tencent"

    def test_queue_type_values(self):
        """
        场景：队列类型枚举
        WHEN: 访问枚举值
        THEN: 返回正确字符串
        """
        assert QueueType.REDIS.value == "redis"
        assert QueueType.RABBITMQ.value == "rabbitmq"
        assert QueueType.KAFKA.value == "kafka"


class TestResourceConfigs:
    """资源配置测试"""

    def test_database_config_defaults(self):
        """
        场景：数据库配置默认值
        WHEN: 创建 TenantDatabaseConfig 不传参数
        THEN: 默认 type 为 POSTGRESQL，port 为 5432
        """
        config = TenantDatabaseConfig()
        assert config.type == DatabaseType.POSTGRESQL
        assert config.port == 5432
        assert config.host == ""
        assert config.database == ""

    def test_database_config_custom(self):
        """
        场景：自定义数据库配置
        WHEN: 创建 TenantDatabaseConfig 传入参数
        THEN: 正确存储配置
        """
        config = TenantDatabaseConfig(
            type=DatabaseType.MYSQL,
            host="localhost",
            port=3306,
            database="tenant_db",
        )
        assert config.type == DatabaseType.MYSQL
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.database == "tenant_db"

    def test_storage_config_defaults(self):
        """
        场景：存储配置默认值
        WHEN: 创建 TenantStorageConfig 不传参数
        THEN: 默认 type 为 MINIO
        """
        config = TenantStorageConfig()
        assert config.type == StorageType.MINIO

    def test_queue_config_defaults(self):
        """
        场景：队列配置默认值
        WHEN: 创建 TenantQueueConfig 不传参数
        THEN: 默认 type 为 REDIS
        """
        config = TenantQueueConfig()
        assert config.type == QueueType.REDIS


class TestSimpleTenant:
    """SimpleTenant 测试"""

    def test_tenant_creation(self):
        """
        场景：创建租户
        WHEN: 初始化 SimpleTenant
        THEN: 正确设置所有属性
        """
        tenant = SimpleTenant(
            id="tenant-123",
            name="测试租户",
            code="test_tenant",
        )

        assert tenant.id == "tenant-123"
        assert tenant.name == "测试租户"
        assert tenant.code == "test_tenant"
        assert tenant.status == "active"

    def test_tenant_with_database_config(self):
        """
        场景：租户数据库配置
        WHEN: 设置数据库配置
        THEN: 正确存储配置
        """
        tenant = SimpleTenant(
            id="tenant-123",
            name="测试租户",
            code="test_tenant",
            database=TenantDatabaseConfig(
                type=DatabaseType.POSTGRESQL,
                host="localhost",
                port=5432,
                database="tenant_db",
            ),
        )

        assert tenant.database is not None
        assert tenant.database.type == DatabaseType.POSTGRESQL
        assert tenant.database.host == "localhost"
        assert tenant.database.port == 5432

    def test_tenant_default_values(self):
        """
        场景：默认值
        WHEN: 创建租户不设置某些字段
        THEN: 联系人和资源配置为 None
        """
        tenant = SimpleTenant(
            id="tenant-123",
            name="测试租户",
            code="test_tenant",
        )

        assert tenant.contact_name is None
        assert tenant.database is None
        assert tenant.storage is None
        assert tenant.queue is None
        assert tenant.pubsub is None

    def test_from_model(self):
        """
        场景：从 ORM 模型创建
        WHEN: 调用 SimpleTenant.from_model
        THEN: 正确提取字段
        """

        class MockORMModel:
            id = "orm-123"
            name = "ORM租户"
            code = "orm_tenant"
            status = "active"
            contact_name = "张三"
            contact_email = "test@example.com"
            contact_phone = "13800138000"

        tenant = SimpleTenant.from_model(MockORMModel())

        assert tenant.id == "orm-123"
        assert tenant.name == "ORM租户"
        assert tenant.code == "orm_tenant"
        assert tenant.status == "active"
        assert tenant.contact_name == "张三"
        assert tenant.contact_email == "test@example.com"
        assert tenant.contact_phone == "13800138000"


class TestTenantProviderRegistration:
    """TenantProvider 注册测试"""

    def setup_method(self):
        """每个测试前重置 provider"""
        import framework.tenant.protocols as proto
        proto._tenant_provider = None

    def test_register_and_get(self):
        """
        场景：启动时注册
        WHEN: 调用 register_tenant_provider 后 get_tenant_provider
        THEN: 返回注册的实例
        """

        class MockProvider:
            async def get_tenant(self, tenant_id): return None
            async def validate_access(self, user_id, tenant_id): return False
            async def get_user_tenants(self, user_id): return []

        provider = MockProvider()
        register_tenant_provider(provider)
        assert get_tenant_provider() is provider

    def test_unregistered_raises(self):
        """
        场景：未注册时访问
        WHEN: 未调用 register_tenant_provider 时调用 get_tenant_provider
        THEN: 抛出 RuntimeError
        """
        with pytest.raises(RuntimeError, match="TenantProvider not registered"):
            get_tenant_provider()


class TestTenantContext:
    """租户上下文测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        TenantContext.clear()

    def test_set_and_get_tenant(self):
        """
        场景：设置和获取租户
        WHEN: 设置当前租户
        THEN: 可以获取到
        """
        tenant = SimpleTenant(
            id="tenant-123",
            name="测试租户",
            code="test_tenant",
        )

        set_current_tenant(tenant)
        result = get_current_tenant()

        assert result is not None
        assert result.id == "tenant-123"

    def test_get_tenant_id(self):
        """
        场景：获取租户 ID
        WHEN: 设置租户后获取 ID
        THEN: 返回正确 ID
        """
        tenant = SimpleTenant(
            id="tenant-456",
            name="测试租户",
            code="test_tenant",
        )

        set_current_tenant(tenant)
        assert get_tenant_id() == "tenant-456"

    def test_get_tenant_id_none(self):
        """
        场景：未设置租户
        WHEN: 获取租户 ID
        THEN: 返回 None
        """
        assert get_tenant_id() is None

    def test_clear_context(self):
        """
        场景：清理上下文
        WHEN: 设置租户后清理
        THEN: 租户被清除
        """
        tenant = SimpleTenant(
            id="tenant-123",
            name="测试租户",
            code="test_tenant",
        )

        set_current_tenant(tenant)
        TenantContext.clear()
        assert get_current_tenant() is None

    def test_context_isolation(self):
        """
        场景：上下文隔离
        WHEN: 多次设置不同租户
        THEN: 返回最后设置的租户
        """
        tenant1 = SimpleTenant(id="tenant-1", name="租户1", code="t1")
        tenant2 = SimpleTenant(id="tenant-2", name="租户2", code="t2")

        set_current_tenant(tenant1)
        set_current_tenant(tenant2)

        assert get_tenant_id() == "tenant-2"
