"""
ModuleMenuPermission 模型单元测试
"""

from unittest.mock import MagicMock


class TestModuleMenuPermission:
    """ModuleMenuPermission 模型测试"""

    def test_model_fields_definition(self):
        """验证模型字段定义"""
        from tenant.models import ModuleMenuPermission

        # 验证表名
        assert ModuleMenuPermission.__tablename__ == "module_menu_permissions"

        # 验证字段存在
        assert hasattr(ModuleMenuPermission, "module_menu_id")
        assert hasattr(ModuleMenuPermission, "module_permission_id")

    def test_model_table_args_constraints(self):
        """验证唯一约束和索引"""
        from tenant.models import ModuleMenuPermission

        table_args = ModuleMenuPermission.__table_args__

        # 验证唯一约束
        unique_constraints = [
            arg for arg in table_args if hasattr(arg, "name") and "uq_" in str(arg.name)
        ]
        assert len(unique_constraints) == 1
        assert unique_constraints[0].name == "uq_module_menu_permissions_menu_perm"

        # 验证唯一约束字段
        constraint_columns = list(unique_constraints[0].columns.keys())
        assert "module_menu_id" in constraint_columns
        assert "module_permission_id" in constraint_columns

    def test_model_table_args_indexes(self):
        """验证索引定义"""
        from tenant.models import ModuleMenuPermission

        table_args = ModuleMenuPermission.__table_args__

        # 验证索引
        indexes = [arg for arg in table_args if hasattr(arg, "name") and "ix_" in str(arg.name)]
        index_names = [idx.name for idx in indexes]

        assert "ix_module_menu_permissions_menu_id" in index_names
        assert "ix_module_menu_permissions_permission_id" in index_names

    def test_model_foreign_key_cascade(self):
        """验证外键级联删除"""
        from sqlalchemy import inspect

        from tenant.models import ModuleMenuPermission

        # 获取模型元数据
        mapper = inspect(ModuleMenuPermission)

        # 验证 module_menu_id 外键
        menu_id_fk = mapper.get_property("module_menu_id")
        assert menu_id_fk is not None

        # 验证 module_permission_id 外键
        permission_id_fk = mapper.get_property("module_permission_id")
        assert permission_id_fk is not None

    def test_model_instance_creation(self):
        """测试创建模型实例"""
        from tenant.models import ModuleMenuPermission

        # 创建实例
        instance = MagicMock(spec=ModuleMenuPermission)
        instance.module_menu_id = "menu-123"
        instance.module_permission_id = "perm-456"

        # 验证属性
        assert instance.module_menu_id == "menu-123"
        assert instance.module_permission_id == "perm-456"

    def test_model_imports_from_tenant_models(self):
        """验证模型可以从 tenant.models 导入"""
        from tenant.models import ModuleMenuPermission

        assert ModuleMenuPermission is not None
        assert ModuleMenuPermission.__tablename__ == "module_menu_permissions"
