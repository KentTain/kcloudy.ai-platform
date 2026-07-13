"""
IAM 模块定义单元测试

验证 get_module_definition() 返回的正确性，包括：
- 所有一级菜单
- 隐藏的二级菜单（create/detail/edit）
"""


class TestIAMModuleDefinition:
    """IAM 模块定义测试"""

    def _get_module_definition(self):
        """获取 IAMModule 的模块定义"""
        from iam.module import IAMModule

        module = IAMModule()
        return module.get_module_definition()

    def test_module_basic_info(self):
        """验证模块基本信息"""
        definition = self._get_module_definition()
        assert definition.code == "iam"
        assert definition.name == "系统管理"
        assert definition.version == "1.0.0"

    def test_top_level_menus_exist(self):
        """验证一级菜单存在"""
        definition = self._get_module_definition()
        menus = definition.menus

        top_level = [m for m in menus if m.parent_code is None]
        top_codes = {m.code for m in top_level}

        assert "iam.organizations" in top_codes
        assert "iam.roles" in top_codes
        assert "iam.users" in top_codes
        assert "iam.menus" in top_codes
        assert "iam.permissions" in top_codes
        assert "iam.audit_logs" in top_codes
        assert len(top_level) >= 6

    def test_top_level_menus_visibility(self):
        """验证一级菜单可见"""
        definition = self._get_module_definition()
        menus = definition.menus

        top_level = [m for m in menus if m.parent_code is None]
        for menu in top_level:
            assert menu.is_visible is True, f"{menu.code} 应该可见"

    def test_organizations_sub_menus(self):
        """验证 organizations 下的隐藏二级菜单"""
        definition = self._get_module_definition()
        menus = definition.menus

        sub_menus = [m for m in menus if m.parent_code == "iam.organizations"]
        sub_codes = {m.code for m in sub_menus}

        expected = {
            "iam.organizations.create",
            "iam.organizations.detail",
            "iam.organizations.edit",
        }
        assert sub_codes == expected

        # 验证每个子菜单
        create = next(m for m in sub_menus if m.code == "iam.organizations.create")
        assert create.path == "/iam/organizations/create"
        assert create.is_visible is False
        assert create.permission_codes == ["iam:organization:write"]

        detail = next(m for m in sub_menus if m.code == "iam.organizations.detail")
        assert detail.path == "/iam/organizations/{id}"
        assert detail.is_visible is False
        assert detail.permission_codes == ["iam:organization:read"]

        edit = next(m for m in sub_menus if m.code == "iam.organizations.edit")
        assert edit.path == "/iam/organizations/{id}/edit"
        assert edit.is_visible is False
        assert edit.permission_codes == ["iam:organization:write"]

    def test_roles_sub_menus(self):
        """验证 roles 下的隐藏二级菜单"""
        definition = self._get_module_definition()
        menus = definition.menus

        sub_menus = [m for m in menus if m.parent_code == "iam.roles"]
        sub_codes = {m.code for m in sub_menus}

        expected = {"iam.roles.create", "iam.roles.detail", "iam.roles.edit"}
        assert sub_codes == expected

        # 验证每个子菜单
        create = next(m for m in sub_menus if m.code == "iam.roles.create")
        assert create.path == "/iam/roles/create"
        assert create.is_visible is False
        assert create.permission_codes == ["iam:role:write"]

        detail = next(m for m in sub_menus if m.code == "iam.roles.detail")
        assert detail.path == "/iam/roles/{id}"
        assert detail.is_visible is False
        assert detail.permission_codes == ["iam:role:read"]

        edit = next(m for m in sub_menus if m.code == "iam.roles.edit")
        assert edit.path == "/iam/roles/{id}/edit"
        assert edit.is_visible is False
        assert edit.permission_codes == ["iam:role:write"]

    def test_users_sub_menus(self):
        """验证 users 下的隐藏二级菜单"""
        definition = self._get_module_definition()
        menus = definition.menus

        sub_menus = [m for m in menus if m.parent_code == "iam.users"]
        sub_codes = {m.code for m in sub_menus}

        expected = {"iam.users.create", "iam.users.detail", "iam.users.edit"}
        assert sub_codes == expected

        # 验证每个子菜单
        create = next(m for m in sub_menus if m.code == "iam.users.create")
        assert create.path == "/iam/users/create"
        assert create.is_visible is False
        assert create.permission_codes == ["iam:user:write"]

        detail = next(m for m in sub_menus if m.code == "iam.users.detail")
        assert detail.path == "/iam/users/{id}"
        assert detail.is_visible is False
        assert detail.permission_codes == ["iam:user:read"]

        edit = next(m for m in sub_menus if m.code == "iam.users.edit")
        assert edit.path == "/iam/users/{id}/edit"
        assert edit.is_visible is False
        assert edit.permission_codes == ["iam:user:write"]

    def test_menus_sub_menus(self):
        """验证 menus 下的隐藏二级菜单"""
        definition = self._get_module_definition()
        menus = definition.menus

        sub_menus = [m for m in menus if m.parent_code == "iam.menus"]
        sub_codes = {m.code for m in sub_menus}

        expected = {"iam.menus.create", "iam.menus.detail", "iam.menus.edit"}
        assert sub_codes == expected

        # 验证每个子菜单
        create = next(m for m in sub_menus if m.code == "iam.menus.create")
        assert create.path == "/iam/menus/create"
        assert create.is_visible is False
        assert create.permission_codes == ["iam:menu:write"]

        detail = next(m for m in sub_menus if m.code == "iam.menus.detail")
        assert detail.path == "/iam/menus/{id}"
        assert detail.is_visible is False
        assert detail.permission_codes == ["iam:menu:read"]

        edit = next(m for m in sub_menus if m.code == "iam.menus.edit")
        assert edit.path == "/iam/menus/{id}/edit"
        assert edit.is_visible is False
        assert edit.permission_codes == ["iam:menu:write"]

    def test_permissions_sub_menus(self):
        """验证 permissions 下的隐藏二级菜单"""
        definition = self._get_module_definition()
        menus = definition.menus

        sub_menus = [m for m in menus if m.parent_code == "iam.permissions"]
        sub_codes = {m.code for m in sub_menus}

        expected = {
            "iam.permissions.create",
            "iam.permissions.detail",
            "iam.permissions.edit",
        }
        assert sub_codes == expected

        # 验证每个子菜单
        create = next(m for m in sub_menus if m.code == "iam.permissions.create")
        assert create.path == "/iam/permissions/create"
        assert create.is_visible is False
        assert create.permission_codes == ["iam:permission:write"]

        detail = next(m for m in sub_menus if m.code == "iam.permissions.detail")
        assert detail.path == "/iam/permissions/{id}"
        assert detail.is_visible is False
        assert detail.permission_codes == ["iam:permission:read"]

        edit = next(m for m in sub_menus if m.code == "iam.permissions.edit")
        assert edit.path == "/iam/permissions/{id}/edit"
        assert edit.is_visible is False
        assert edit.permission_codes == ["iam:permission:write"]
