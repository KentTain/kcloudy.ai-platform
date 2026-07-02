"""
租户模块定义单元测试

验证 get_module_definition() 返回的正确性，包括：
- 所有一级菜单
- 隐藏的二级菜单（create/detail/edit）
- 默认角色定义
"""


class TestTenantModuleDefinition:
    """Tenant 模块定义测试"""

    def _get_module_definition(self):
        """获取 TenantModule 的模块定义"""
        from tenant.module import TenantModule

        module = TenantModule()
        return module.get_module_definition()

    def test_module_basic_info(self):
        """验证模块基本信息"""
        definition = self._get_module_definition()
        assert definition.code == "tenant"
        assert definition.name == "租户管理"
        assert definition.version == "1.0.0"

    def test_top_level_menus_exist(self):
        """验证一级菜单存在"""
        definition = self._get_module_definition()
        menus = definition.menus

        top_level = [m for m in menus if m.parent_code is None]
        top_codes = {m.code for m in top_level}

        assert "tenant.modules" in top_codes
        assert "tenant.tenants" in top_codes
        assert "tenant.resources" in top_codes
        assert "tenant.plugin-definitions" in top_codes
        assert "tenant.marketplaces" in top_codes
        assert len(top_level) >= 5

    def test_top_level_menus_visibility(self):
        """验证一级菜单可见"""
        definition = self._get_module_definition()
        menus = definition.menus

        top_level = [m for m in menus if m.parent_code is None]
        for menu in top_level:
            assert menu.is_visible is True, f"{menu.code} 应该可见"

    def test_modules_sub_menus(self):
        """验证 modules 下的隐藏二级菜单"""
        definition = self._get_module_definition()
        menus = definition.menus

        sub_menus = [m for m in menus if m.parent_code == "tenant.modules"]
        sub_codes = {m.code for m in sub_menus}

        expected = {
            "tenant.modules.create",
            "tenant.modules.detail",
            "tenant.modules.edit",
        }
        assert sub_codes == expected, f"modules 子菜单缺失: {expected - sub_codes}"

        # 验证每个子菜单
        create = next(m for m in sub_menus if m.code == "tenant.modules.create")
        assert create.path == "/admin/modules/create"
        assert create.is_visible is False
        assert create.permission_codes == ["tenant:module:write"]

        detail = next(m for m in sub_menus if m.code == "tenant.modules.detail")
        assert detail.path == "/admin/modules/{id}"
        assert detail.is_visible is False
        assert detail.permission_codes == ["tenant:module:read"]

        edit = next(m for m in sub_menus if m.code == "tenant.modules.edit")
        assert edit.path == "/admin/modules/{id}/edit"
        assert edit.is_visible is False
        assert edit.permission_codes == ["tenant:module:write"]

    def test_tenants_sub_menus(self):
        """验证 tenants 下的隐藏二级菜单"""
        definition = self._get_module_definition()
        menus = definition.menus

        sub_menus = [m for m in menus if m.parent_code == "tenant.tenants"]
        sub_codes = {m.code for m in sub_menus}

        expected = {
            "tenant.tenants.create",
            "tenant.tenants.detail",
            "tenant.tenants.edit",
        }
        assert sub_codes == expected, f"tenants 子菜单缺失: {expected - sub_codes}"

        # 验证每个子菜单
        create = next(m for m in sub_menus if m.code == "tenant.tenants.create")
        assert create.path == "/admin/tenants/create"
        assert create.is_visible is False
        assert create.permission_codes == ["tenant:tenant:write"]

        detail = next(m for m in sub_menus if m.code == "tenant.tenants.detail")
        assert detail.path == "/admin/tenants/{id}"
        assert detail.is_visible is False
        assert detail.permission_codes == ["tenant:tenant:read"]

        edit = next(m for m in sub_menus if m.code == "tenant.tenants.edit")
        assert edit.path == "/admin/tenants/{id}/edit"
        assert edit.is_visible is False
        assert edit.permission_codes == ["tenant:tenant:write"]

    def test_resources_sub_menus(self):
        """验证 resources 下的隐藏二级菜单"""
        definition = self._get_module_definition()
        menus = definition.menus

        sub_menus = [m for m in menus if m.parent_code == "tenant.resources"]
        sub_codes = {m.code for m in sub_menus}

        expected = {
            "tenant.resources.create",
            "tenant.resources.detail",
            "tenant.resources.edit",
        }
        assert sub_codes == expected, f"resources 子菜单缺失: {expected - sub_codes}"

        # 验证每个子菜单
        create = next(m for m in sub_menus if m.code == "tenant.resources.create")
        assert create.path == "/admin/resources/create"
        assert create.is_visible is False
        assert create.permission_codes == ["tenant:resource:write"]

        detail = next(m for m in sub_menus if m.code == "tenant.resources.detail")
        assert detail.path == "/admin/resources/{id}"
        assert detail.is_visible is False
        assert detail.permission_codes == ["tenant:resource:read"]

        edit = next(m for m in sub_menus if m.code == "tenant.resources.edit")
        assert edit.path == "/admin/resources/{id}/edit"
        assert edit.is_visible is False
        assert edit.permission_codes == ["tenant:resource:write"]

    def test_default_roles_exist(self):
        """验证默认角色定义"""
        definition = self._get_module_definition()
        assert definition.default_roles is not None
        assert len(definition.default_roles) == 2

        roles = {r.code: r for r in definition.default_roles}

        # tenantAdmin
        assert "tenantAdmin" in roles
        admin_role = roles["tenantAdmin"]
        assert admin_role.name == "租户管理员"
        assert admin_role.description == "拥有租户管理模块的所有读写权限"
        assert admin_role.permission_codes == ["tenant:*:*"]
        assert admin_role.is_system is True

        # ordinaryAdmin
        assert "ordinaryAdmin" in roles
        ordinary_role = roles["ordinaryAdmin"]
        assert ordinary_role.name == "普通管理员"
        assert ordinary_role.description == "拥有租户管理模块的只读权限"
        assert ordinary_role.permission_codes == ["tenant:*:read"]
        assert ordinary_role.is_system is True
