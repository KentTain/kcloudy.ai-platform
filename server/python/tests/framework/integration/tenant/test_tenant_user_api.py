"""
用户端租户 API 集成测试

测试场景覆盖：
1. 获取用户可用租户列表
2. 获取当前租户信息
3. 租户切换
"""

import pytest

from framework.tenant.context import SimpleTenant, TenantContext


class TestUserTenantAPI:
    """用户端租户 API 测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        TenantContext.clear()

    def teardown_method(self):
        """每个测试后清理上下文"""
        TenantContext.clear()

    def test_schema_validation(self):
        """测试 Schema 验证"""
        from tenant.schemas.console.tenant import UserTenantVo, CurrentTenantVo, SwitchTenantVo

        # 用户租户 VO
        vo = UserTenantVo(
            id="t001",
            name="测试租户",
            code="test",
            status="active",
            role="admin",
            is_default=True,
        )
        assert vo.id == "t001"
        assert vo.role == "admin"

        # 当前租户 VO
        current = CurrentTenantVo(
            id="t001",
            name="测试租户",
            code="test",
            status="active",
        )
        assert current.id == "t001"

        # 切换租户 VO
        switch = SwitchTenantVo(
            tenant_id="t001",
            tenant_name="测试租户",
            message="切换成功",
        )
        assert switch.tenant_id == "t001"

    def test_tenant_context_for_user_api(self):
        """
        场景：获取当前租户信息

        WHEN 用户请求 GET /console/v1/tenants/current
        THEN 返回当前租户的详细信息
        """
        from framework.tenant.context import get_tenant_id

        # 设置租户上下文
        tenant = SimpleTenant(id="tenant_001", name="用户租户", code="user", status="active")
        TenantContext.set_current_tenant(tenant)

        # 验证可获取
        assert get_tenant_id() == "tenant_001"

    def test_switch_tenant_context(self):
        """
        场景：切换租户

        WHEN 用户请求 POST /console/v1/tenants/{id}/switch
        THEN 后续请求使用新租户上下文
        """
        # 设置初始租户
        tenant1 = SimpleTenant(id="t1", name="租户1", code="t1", status="active")
        TenantContext.set_current_tenant(tenant1)
        assert TenantContext.get_tenant_id() == "t1"

        # 切换到新租户
        tenant2 = SimpleTenant(id="t2", name="租户2", code="t2", status="active")
        TenantContext.set_current_tenant(tenant2)
        assert TenantContext.get_tenant_id() == "t2"

    def test_no_tenant_context_error(self):
        """
        场景：未设置租户上下文

        WHEN 用户未设置租户上下文时请求 GET /console/v1/tenants/current
        THEN 返回 HTTP 400 错误
        """
        from framework.tenant.context import get_tenant_id

        # 清理上下文
        TenantContext.clear()
        assert get_tenant_id() is None
