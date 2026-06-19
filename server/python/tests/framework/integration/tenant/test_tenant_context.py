"""
租户上下文集成测试

测试场景覆盖：
1. 租户上下文的设置和获取
2. 线程/协程隔离
3. 上下文清理
"""

import asyncio

import pytest

from framework.tenant.context import (
    SimpleTenant,
    TenantContext,
    clear_tenant_context,
    get_current_tenant,
    get_tenant_id,
    set_current_tenant,
)


class TestTenantContextIntegration:
    """租户上下文集成测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        TenantContext.clear()

    def teardown_method(self):
        """每个测试后清理上下文"""
        TenantContext.clear()

    def test_full_lifecycle(self):
        """
        场景：完整的上下文生命周期

        WHEN 设置租户上下文 -> 获取信息 -> 清理上下文
        THEN 每个步骤都按预期工作
        """
        # 1. 初始状态为空
        assert get_tenant_id() is None
        assert get_current_tenant() is None

        # 2. 设置租户
        tenant = SimpleTenant(
            id="tenant_001",
            name="测试租户",
            code="test",
            status="active",
        )
        set_current_tenant(tenant)

        # 3. 验证可获取
        assert get_tenant_id() == "tenant_001"
        current = get_current_tenant()
        assert current is not None
        assert current.name == "测试租户"

        # 4. 清理
        clear_tenant_context()
        assert get_tenant_id() is None
        assert get_current_tenant() is None

    def test_context_overwrite(self):
        """
        场景：覆盖租户上下文

        WHEN 连续设置不同的租户
        THEN 最后设置的租户生效
        """
        tenant1 = SimpleTenant(id="t1", name="租户1", code="t1", status="active")
        tenant2 = SimpleTenant(id="t2", name="租户2", code="t2", status="active")

        set_current_tenant(tenant1)
        assert get_tenant_id() == "t1"

        set_current_tenant(tenant2)
        assert get_tenant_id() == "t2"

    def test_multiple_clears(self):
        """
        场景：多次清理上下文

        WHEN 多次调用 clear
        THEN 不会出错，状态保持为空
        """
        clear_tenant_context()
        clear_tenant_context()
        clear_tenant_context()
        assert get_tenant_id() is None

    @pytest.mark.asyncio
    async def test_async_tasks_isolation(self):
        """
        场景：异步任务间上下文隔离

        WHEN 在不同异步任务中设置不同租户
        THEN 各任务互不影响
        """
        results = {}

        async def task_a():
            tenant = SimpleTenant(id="tenant_a", name="A", code="a", status="active")
            set_current_tenant(tenant)
            await asyncio.sleep(0.05)
            results["a"] = get_tenant_id()
            clear_tenant_context()

        async def task_b():
            await asyncio.sleep(0.02)
            tenant = SimpleTenant(id="tenant_b", name="B", code="b", status="active")
            set_current_tenant(tenant)
            results["b"] = get_tenant_id()
            clear_tenant_context()

        await asyncio.gather(task_a(), task_b())

        assert results["a"] == "tenant_a"
        assert results["b"] == "tenant_b"

    def test_simple_tenant_from_model(self):
        """
        场景：从 ORM 模型创建 SimpleTenant

        WHEN 使用 SimpleTenant.from_model()
        THEN 正确提取租户信息
        """
        class MockTenantModel:
            id = "model_001"
            name = "模型租户"
            code = "model"
            status = "active"

        simple = SimpleTenant.from_model(MockTenantModel())
        assert simple.id == "model_001"
        assert simple.name == "模型租户"
        assert simple.code == "model"
        assert simple.status == "active"
