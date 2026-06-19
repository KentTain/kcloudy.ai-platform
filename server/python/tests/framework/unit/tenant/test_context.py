"""
租户上下文单元测试
"""

import asyncio

import pytest

from framework.tenant.context import (
    SimpleTenant,
    TenantContext,
    get_tenant_id,
)


class TestSimpleTenant:
    """SimpleTenant 测试"""

    def test_create_simple_tenant(self):
        """创建 SimpleTenant"""
        tenant = SimpleTenant(
            id="tenant_001",
            name="测试租户",
            code="test",
            status="active",
        )
        assert tenant.id == "tenant_001"
        assert tenant.name == "测试租户"
        assert tenant.code == "test"
        assert tenant.status == "active"

    def test_from_model(self):
        """从 ORM 模型创建 SimpleTenant"""

        class MockTenant:
            id = "tenant_002"
            name = "模拟租户"
            code = "mock"
            status = "inactive"

        tenant = SimpleTenant.from_model(MockTenant())
        assert tenant.id == "tenant_002"
        assert tenant.name == "模拟租户"
        assert tenant.code == "mock"
        assert tenant.status == "inactive"


class TestTenantContext:
    """TenantContext 测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        TenantContext.clear()

    def teardown_method(self):
        """每个测试后清理上下文"""
        TenantContext.clear()

    def test_set_and_get_current_tenant(self):
        """场景：设置租户上下文"""
        tenant = SimpleTenant(
            id="tenant_001",
            name="测试租户",
            code="test",
            status="active",
        )

        TenantContext.set_current_tenant(tenant)
        result = TenantContext.get_current_tenant()

        assert result is not None
        assert result.id == "tenant_001"
        assert result.name == "测试租户"

    def test_get_nonexistent_tenant_context(self):
        """场景：获取不存在的租户上下文"""
        result = TenantContext.get_current_tenant()
        assert result is None

    def test_get_tenant_id(self):
        """场景：获取租户 ID"""
        tenant = SimpleTenant(
            id="tenant_001",
            name="测试租户",
            code="test",
            status="active",
        )
        TenantContext.set_current_tenant(tenant)

        result = get_tenant_id()
        assert result == "tenant_001"

    def test_get_tenant_id_when_not_set(self):
        """场景：未设置租户上下文时获取租户 ID"""
        result = get_tenant_id()
        assert result is None

    def test_clear_tenant_context(self):
        """场景：清理租户上下文"""
        tenant = SimpleTenant(
            id="tenant_001",
            name="测试租户",
            code="test",
            status="active",
        )
        TenantContext.set_current_tenant(tenant)
        assert TenantContext.get_current_tenant() is not None

        TenantContext.clear()
        assert TenantContext.get_current_tenant() is None

    def test_is_set(self):
        """测试 is_set 方法"""
        assert TenantContext.is_set() is False

        tenant = SimpleTenant(
            id="tenant_001",
            name="测试租户",
            code="test",
            status="active",
        )
        TenantContext.set_current_tenant(tenant)
        assert TenantContext.is_set() is True

        TenantContext.clear()
        assert TenantContext.is_set() is False


class TestTenantContextAsync:
    """TenantContext 异步测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        TenantContext.clear()

    def teardown_method(self):
        """每个测试后清理上下文"""
        TenantContext.clear()

    @pytest.mark.asyncio
    async def test_async_context_isolation(self):
        """测试异步上下文隔离"""
        tenant1 = SimpleTenant(id="tenant_001", name="租户1", code="t1", status="active")
        tenant2 = SimpleTenant(id="tenant_002", name="租户2", code="t2", status="active")

        results = []

        async def task1():
            TenantContext.set_current_tenant(tenant1)
            await asyncio.sleep(0.1)
            results.append(("task1", TenantContext.get_tenant_id()))

        async def task2():
            await asyncio.sleep(0.05)
            TenantContext.set_current_tenant(tenant2)
            results.append(("task2", TenantContext.get_tenant_id()))

        await asyncio.gather(task1(), task2())

        # 验证每个任务获取到正确的租户 ID
        assert ("task1", "tenant_001") in results
        assert ("task2", "tenant_002") in results
