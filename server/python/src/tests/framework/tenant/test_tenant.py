"""
tenant 模块单元测试
"""

import pytest
from datetime import datetime

from framework.tenant.models import Tenant, TenantSetting, TenantDatabaseConfig
from framework.tenant.enums import DatabaseType, StorageType, QueueType
from framework.tenant.context import TenantContext, get_current_tenant, set_current_tenant, get_tenant_id


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


class TestTenantModel:
    """租户模型测试"""

    def test_tenant_creation(self):
        """
        场景：创建租户
        WHEN: 初始化 Tenant
        THEN: 正确设置所有属性
        """
        tenant = Tenant(
            id="tenant-123",
            name="测试租户",
            code="test_tenant"
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
        tenant = Tenant(
            id="tenant-123",
            name="测试租户",
            code="test_tenant",
            database=TenantDatabaseConfig(
                type=DatabaseType.POSTGRESQL,
                host="localhost",
                port=5432,
                database="tenant_db"
            )
        )

        assert tenant.database.type == DatabaseType.POSTGRESQL
        assert tenant.database.host == "localhost"
        assert tenant.database.port == 5432

    def test_tenant_default_values(self):
        """
        场景：默认值
        WHEN: 创建租户不设置某些字段
        THEN: 使用默认值
        """
        tenant = Tenant(
            id="tenant-123",
            name="测试租户",
            code="test_tenant"
        )

        assert tenant.settings == {}
        assert tenant.contact_name == ""
        assert tenant.expired_at is None


class TestTenantSetting:
    """租户设置测试"""

    def test_tenant_setting_creation(self):
        """
        场景：创建租户设置
        WHEN: 初始化 TenantSetting
        THEN: 正确设置所有属性
        """
        setting = TenantSetting(
            tenant_id="tenant-123",
            name="theme",
            value="dark"
        )

        assert setting.tenant_id == "tenant-123"
        assert setting.name == "theme"
        assert setting.value == "dark"


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
        tenant = Tenant(
            id="tenant-123",
            name="测试租户",
            code="test_tenant"
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
        tenant = Tenant(
            id="tenant-456",
            name="测试租户",
            code="test_tenant"
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
        tenant = Tenant(
            id="tenant-123",
            name="测试租户",
            code="test_tenant"
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
        tenant1 = Tenant(id="tenant-1", name="租户1", code="t1")
        tenant2 = Tenant(id="tenant-2", name="租户2", code="t2")

        set_current_tenant(tenant1)
        set_current_tenant(tenant2)

        assert get_tenant_id() == "tenant-2"
