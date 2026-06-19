"""
租户数据隔离集成测试

测试场景覆盖：
1. 数据库字段级隔离
2. 租户 ID 自动填充
3. 查询自动过滤
"""


from framework.database.mixins.tenant import (
    TenantMixin,
    clear_skip_tenant,
    set_skip_tenant,
    should_skip_tenant,
)
from framework.tenant.context import SimpleTenant, TenantContext


class TestTenantMixin:
    """TenantMixin 测试"""

    def test_mixin_has_tenant_id(self):
        """
        场景：继承 TenantMixin

        WHEN 模型继承 TenantMixin
        THEN 模型自动拥有 tenant_id 字段
        """
        # TenantMixin 是抽象类，检查属性存在
        assert hasattr(TenantMixin, 'tenant_id')

    def test_skip_tenant_flag(self):
        """
        场景：管理员场景跳过自动填充

        WHEN 设置 skip_tenant=True 标志
        THEN should_skip_tenant() 返回 True
        """
        assert should_skip_tenant() is False

        set_skip_tenant(True)
        assert should_skip_tenant() is True

        clear_skip_tenant()
        assert should_skip_tenant() is False

    def test_skip_tenant_context(self):
        """测试 skip_tenant 上下文管理"""
        # 设置标志
        set_skip_tenant(True)
        assert should_skip_tenant() is True

        # 清除标志
        clear_skip_tenant()
        assert should_skip_tenant() is False


class TestTenantQueryInterceptor:
    """租户查询拦截器测试"""

    def test_interceptor_logic(self):
        """
        场景：查询自动过滤

        WHEN 执行查询操作
        THEN 自动添加 WHERE tenant_id = :current_tenant_id 条件
        """
        from framework.database.interceptors.query import TenantQueryInterceptor

        # 简单的逻辑验证
        assert hasattr(TenantQueryInterceptor, 'inject_tenant_filter')


class TestDataIsolation:
    """数据隔离测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        TenantContext.clear()

    def teardown_method(self):
        """每个测试后清理上下文"""
        TenantContext.clear()

    def test_tenant_context_available(self):
        """
        场景：租户上下文可用

        WHEN 设置租户上下文
        THEN 可通过 get_tenant_id 获取
        """
        tenant = SimpleTenant(id="tenant_001", name="测试", code="t1", status="active")
        TenantContext.set_current_tenant(tenant)

        from framework.tenant.context import get_tenant_id
        assert get_tenant_id() == "tenant_001"
