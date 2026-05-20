"""
测试 demo 模块从 framework 导入的行为

遵循 TDD：先写测试验证期望的导入行为，然后重构代码使测试通过。
"""

import pytest


class TestDemoConfigsImports:
    """测试 demo.configs 模块从 framework 导入"""

    def test_import_base_settings_from_framework(self):
        """demo.configs 应该从 framework 导入 BaseSettings"""
        from demo.configs import BaseSettings

        # 验证来自 framework
        from framework.config.base import BaseSettings as FrameworkBaseSettings

        assert BaseSettings is FrameworkBaseSettings

    def test_import_yaml_parser_from_framework(self):
        """demo.configs 应该从 framework 导入 YamlParser"""
        from demo.configs import YamlParser

        from framework.config.yaml import YamlParser as FrameworkYamlParser

        assert YamlParser is FrameworkYamlParser

    def test_import_helpers_from_framework(self):
        """demo.configs 应该从 framework 导入 helper 函数"""
        from demo.configs import (
            hyphen_to_underscore,
            convert_dict_hyphen_to_underscore,
        )

        from framework.config.helpers import (
            hyphen_to_underscore as framework_hyphen,
            convert_dict_hyphen_to_underscore as framework_convert,
        )

        assert hyphen_to_underscore is framework_hyphen
        assert convert_dict_hyphen_to_underscore is framework_convert


class TestDemoCommonImports:
    """测试 demo.common 模块从 framework 导入"""

    def test_import_exceptions_from_framework(self):
        """demo.common 应该从 framework 导入异常类"""
        from demo.common import (
            UnauthorizedError,
            ForbiddenError,
            NotFoundError,
            BadRequestError,
        )

        from framework.common.exceptions import (
            UnauthorizedError as FrameworkUnauthorized,
            ForbiddenError as FrameworkForbidden,
            NotFoundError as FrameworkNotFound,
            BadRequestError as FrameworkBadRequest,
        )

        assert UnauthorizedError is FrameworkUnauthorized
        assert ForbiddenError is FrameworkForbidden
        assert NotFoundError is FrameworkNotFound
        assert BadRequestError is FrameworkBadRequest

    def test_import_context_functions_from_framework(self):
        """demo.common 应该从 framework 导入上下文函数"""
        from demo.common import (
            get_context,
            set_context,
            clear_context,
            get_user_id,
            get_tenant_id,
        )

        from framework.common.ctx import (
            get_context as framework_get_context,
            set_context as framework_set_context,
            clear_context as framework_clear_context,
            get_user_id as framework_get_user_id,
            get_tenant_id as framework_get_tenant_id,
        )

        assert get_context is framework_get_context
        assert set_context is framework_set_context
        assert clear_context is framework_clear_context
        assert get_user_id is framework_get_user_id
        assert get_tenant_id is framework_get_tenant_id


class TestDemoUtilsImports:
    """测试 demo.utils 模块的功能"""

    def test_deep_merge_dict_works(self):
        """demo.utils.deep_merge_dict 应该正常工作"""
        from demo.utils import deep_merge_dict

        base = {"a": 1, "b": {"c": 2}}
        override = {"b": {"d": 3}, "e": 4}
        result = deep_merge_dict(base, override)

        assert result == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

    def test_tree_util_available(self):
        """demo.utils.TreeUtil 应该可用"""
        from demo.utils import TreeUtil

        assert hasattr(TreeUtil, "build_tree")
        assert hasattr(TreeUtil, "build_parameter_tree")


class TestDemoCoreCommonImports:
    """测试 demo.core.common 模块的独特功能"""

    def test_env_is_defined(self):
        """demo.core.common 应该定义 ENV 变量"""
        from demo.core.common import ENV

        assert ENV is not None
        assert ENV in ["local", "dev", "test", "prod"]

    def test_path_constants_defined(self):
        """demo.core.common 应该定义路径常量"""
        from demo.core.common import (
            CONFIG_FOLDER,
            LOGS_DIR,
            ROOT_DIR,
            SRC_DIR,
            WORKSPACE_ROOT_DIR,
        )

        assert SRC_DIR is not None
        assert ROOT_DIR is not None
        assert LOGS_DIR is not None
        assert CONFIG_FOLDER is not None
        assert WORKSPACE_ROOT_DIR is not None

    def test_singleton_classes_defined(self):
        """demo.core.common 应该定义单例类"""
        from demo.core.common import Singleton, AbstractSingleton

        assert Singleton is not None
        assert AbstractSingleton is not None

    def test_china_timezone_defined(self):
        """demo.core.common 应该定义 ChinaTimeZone"""
        from demo.core.common import ChinaTimeZone

        assert ChinaTimeZone is not None

    def test_instance_functions_defined(self):
        """demo.core.common 应该定义实例管理函数"""
        from demo.core.common import get_instance_id, set_instance_id

        assert callable(get_instance_id)
        assert callable(set_instance_id)


class TestDemoConfigsNoDuplicateModules:
    """测试 demo.configs 不应该有重复的模块文件"""

    def test_no_duplicate_base_module(self):
        """demo.configs.base 不应该存在（应使用 framework）"""
        import importlib.util

        spec = importlib.util.find_spec("demo.configs.base")
        # 如果模块不存在，spec 应该是 None 或者指向 framework
        # 如果存在独立的 base.py，spec 不应该是 None
        # 这里测试的期望是：base.py 应该被删除或者只是重导出
        if spec is not None and spec.origin is not None:
            # 如果文件存在，检查它是否只是简单的重导出
            import ast

            with open(spec.origin, encoding="utf-8") as f:
                tree = ast.parse(f.read())

            # 检查是否定义了 BaseSettings 类（不应该定义，应该导入）
            class_definitions = [
                node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            ]
            # 应该不定义 BaseSettings 类
            assert "BaseSettings" not in class_definitions, (
                "demo.configs.base 不应该定义 BaseSettings 类，应从 framework 导入"
            )

    def test_no_duplicate_helpers_module(self):
        """demo.configs.helpers 不应该存在（应使用 framework）"""
        import importlib.util

        spec = importlib.util.find_spec("demo.configs.helpers")
        if spec is not None and spec.origin is not None:
            import ast

            with open(spec.origin, encoding="utf-8") as f:
                tree = ast.parse(f.read())

            # 检查是否定义了函数（不应该定义，应该导入）
            function_definitions = [
                node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
            ]
            expected_functions = ["hyphen_to_underscore", "convert_dict_hyphen_to_underscore"]
            for func in expected_functions:
                assert func not in function_definitions, (
                    f"demo.configs.helpers 不应该定义 {func} 函数，应从 framework 导入"
                )


class TestDemoUtilsDictionaryUtil:
    """测试 demo.utils.dictionary_util 的行为"""

    def test_deep_merge_dict_from_demo_or_framework(self):
        """deep_merge_dict 应该正确工作（无论来自哪里）"""
        # 先检查 demo.utils.dictionary_util 是否存在
        import importlib.util

        spec = importlib.util.find_spec("demo.utils.dictionary_util")

        if spec is not None:
            # 如果存在，测试其行为
            from demo.utils.dictionary_util import deep_merge_dict

            result = deep_merge_dict({"a": 1}, {"b": 2})
            assert result == {"a": 1, "b": 2}
        else:
            # 如果不存在，验证从 framework 导入
            from framework.utils.dictionary_util import deep_merge

            result = deep_merge({"a": 1}, {"b": 2})
            assert result == {"a": 1, "b": 2}
