"""
AI 模块定义单元测试

验证 get_module_definition() 返回的基本信息。
菜单和权限结构会经常变动，只做简单测试。
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

    def test_menus_not_empty(self):
        """验证菜单列表不为空"""
        definition = self._get_module_definition()
        assert len(definition.menus) > 0

    def test_permissions_not_empty(self):
        """验证权限列表不为空"""
        definition = self._get_module_definition()
        assert len(definition.permissions) > 0

    def test_top_level_menus(self):
        """验证一级菜单（parent_code is None）"""
        definition = self._get_module_definition()
        menus = definition.menus

        # 筛选一级菜单
        top_level = [m for m in menus if m.parent_code is None]

        # 验证一级菜单数量
        assert len(top_level) >= 1, "至少应有一个一级菜单"

        # 验证一级菜单基本属性
        for menu in top_level:
            assert menu.code.startswith("ai."), "一级菜单 code 应以 'ai.' 开头"
            assert menu.name, "菜单名称不能为空"
            assert menu.path, "菜单路径不能为空"
            assert menu.is_visible is True, "一级菜单应默认可见"

    def test_sub_menus(self):
        """验证二级菜单（parent_code is not None）"""
        definition = self._get_module_definition()
        menus = definition.menus

        # 筛选二级菜单
        sub_menus = [m for m in menus if m.parent_code is not None]

        # 验证二级菜单数量（可能为 0）
        if len(sub_menus) > 0:
            # 验证二级菜单基本属性
            for menu in sub_menus:
                assert menu.parent_code, "二级菜单必须有 parent_code"
                assert menu.code.startswith("ai."), "二级菜单 code 应以 'ai.' 开头"
                # 验证父菜单存在
                parent_codes = {m.code for m in menus}
                assert menu.parent_code in parent_codes, f"父菜单 {menu.parent_code} 不存在"
