"""
AI 模块定义单元测试

验证 get_module_definition() 返回的正确性，包括：
- plugins 菜单的 permission_codes
- 隐藏的二级菜单（create/detail/edit）
"""


class TestAIModuleDefinition:
    """AI 模块定义测试"""

    def _get_module_definition(self):
        """获取 AIModule 的模块定义"""
        from ai.module import AIModule

        module = AIModule()
        return module.get_module_definition()

    def test_module_basic_info(self):
        """验证模块基本信息"""
        definition = self._get_module_definition()
        assert definition.code == "ai"
        assert definition.name == "AI 能力"
        assert definition.version == "1.0.0"

    def test_plugins_menu_has_permission_codes(self):
        """验证 plugins 一级菜单有 permission_codes"""
        definition = self._get_module_definition()
        menus = definition.menus

        plugins_menu = next(m for m in menus if m.code == "ai.plugins")
        assert plugins_menu.permission_codes == ["ai:plugin:read"]
        assert plugins_menu.is_visible is True

    def test_plugins_sub_menus_exist(self):
        """验证 plugins 下的隐藏二级菜单"""
        definition = self._get_module_definition()
        menus = definition.menus

        sub_menus = [m for m in menus if m.parent_code == "ai.plugins"]
        sub_codes = {m.code for m in sub_menus}

        expected = {"ai.plugins.create", "ai.plugins.detail", "ai.plugins.edit"}
        assert sub_codes == expected

    def test_plugins_sub_menus_attributes(self):
        """验证 plugins 隐藏二级菜单的属性"""
        definition = self._get_module_definition()
        menus = definition.menus

        # ai.plugins.create
        create = next(m for m in menus if m.code == "ai.plugins.create")
        assert create.path == "/ai/plugins/create"
        assert create.is_visible is False
        assert create.permission_codes == ["ai:plugin:write"]

        # ai.plugins.detail
        detail = next(m for m in menus if m.code == "ai.plugins.detail")
        assert detail.path == "/ai/plugins/{id}"
        assert detail.is_visible is False
        assert detail.permission_codes == ["ai:plugin:read"]

        # ai.plugins.edit
        edit = next(m for m in menus if m.code == "ai.plugins.edit")
        assert edit.path == "/ai/plugins/{id}/edit"
        assert edit.is_visible is False
        assert edit.permission_codes == ["ai:plugin:write"]

    def test_top_level_menu_count(self):
        """验证一级菜单数量"""
        definition = self._get_module_definition()
        menus = definition.menus

        top_level = [m for m in menus if m.parent_code is None]
        assert len(top_level) == 1
