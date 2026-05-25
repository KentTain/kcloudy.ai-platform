"""
框架层模块系统单元测试
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any

from framework.module import (
    ModuleDescriptor,
    ModuleRegistry,
    get_registry,
    CyclicDependencyError,
    ModuleLoadError,
    discover_modules,
    filter_modules,
    load_modules,
    resolve_dependencies,
)


class TestModuleRegistry:
    """模块注册中心测试"""

    def setup_method(self):
        """每个测试前重置注册中心"""
        ModuleRegistry.reset()

    def test_singleton_pattern(self):
        """测试单例模式"""
        registry1 = ModuleRegistry()
        registry2 = ModuleRegistry()
        assert registry1 is registry2

    def test_get_registry_returns_singleton(self):
        """测试 get_registry 返回单例"""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_register_module(self):
        """测试注册模块"""
        registry = get_registry()
        module = MagicMock(spec=ModuleDescriptor)
        module.name = "test_module"

        registry.register(module)

        assert registry.has_module("test_module")
        assert registry.get_module("test_module") is module

    def test_register_duplicate_module_raises_error(self):
        """测试注册重复模块抛出异常"""
        registry = get_registry()
        module1 = MagicMock(spec=ModuleDescriptor)
        module1.name = "test_module"
        module2 = MagicMock(spec=ModuleDescriptor)
        module2.name = "test_module"

        registry.register(module1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(module2)

    def test_unregister_module(self):
        """测试注销模块"""
        registry = get_registry()
        module = MagicMock(spec=ModuleDescriptor)
        module.name = "test_module"

        registry.register(module)
        registry.unregister("test_module")

        assert not registry.has_module("test_module")
        assert registry.get_module("test_module") is None

    def test_get_all_modules(self):
        """测试获取所有模块"""
        registry = get_registry()
        module1 = MagicMock(spec=ModuleDescriptor)
        module1.name = "module1"
        module2 = MagicMock(spec=ModuleDescriptor)
        module2.name = "module2"

        registry.register(module1)
        registry.register(module2)

        modules = registry.get_all_modules()
        assert len(modules) == 2
        assert module1 in modules
        assert module2 in modules

    def test_get_all_bases(self):
        """测试获取所有 Base"""
        registry = get_registry()
        base1 = type("Base1", (), {})
        base2 = type("Base2", (), {})

        module1 = MagicMock(spec=ModuleDescriptor)
        module1.name = "module1"
        module1.get_base.return_value = base1

        module2 = MagicMock(spec=ModuleDescriptor)
        module2.name = "module2"
        module2.get_base.return_value = base2

        registry.register(module1)
        registry.register(module2)

        bases = registry.get_all_bases()
        assert len(bases) == 2
        assert base1 in bases
        assert base2 in bases

    def test_module_names_property(self):
        """测试模块名列表属性"""
        registry = get_registry()
        module1 = MagicMock(spec=ModuleDescriptor)
        module1.name = "alpha"
        module2 = MagicMock(spec=ModuleDescriptor)
        module2.name = "beta"

        registry.register(module1)
        registry.register(module2)

        names = registry.module_names
        assert set(names) == {"alpha", "beta"}


class TestResolveDependencies:
    """依赖解析测试"""

    def test_no_dependencies(self):
        """测试无依赖模块"""
        module1 = MagicMock(spec=ModuleDescriptor)
        module1.name = "module1"
        module1.dependencies = []

        module2 = MagicMock(spec=ModuleDescriptor)
        module2.name = "module2"
        module2.dependencies = []

        result = resolve_dependencies([module1, module2])

        assert len(result) == 2
        assert module1 in result
        assert module2 in result

    def test_simple_dependency(self):
        """测试简单依赖关系"""
        # iam 无依赖
        iam = MagicMock(spec=ModuleDescriptor)
        iam.name = "iam"
        iam.dependencies = []

        # demo 依赖 iam
        demo = MagicMock(spec=ModuleDescriptor)
        demo.name = "demo"
        demo.dependencies = ["iam"]

        result = resolve_dependencies([demo, iam])

        # iam 应在 demo 之前
        iam_index = next(i for i, m in enumerate(result) if m.name == "iam")
        demo_index = next(i for i, m in enumerate(result) if m.name == "demo")
        assert iam_index < demo_index

    def test_chain_dependencies(self):
        """测试链式依赖"""
        # a -> b -> c
        a = MagicMock(spec=ModuleDescriptor)
        a.name = "a"
        a.dependencies = ["b"]

        b = MagicMock(spec=ModuleDescriptor)
        b.name = "b"
        b.dependencies = ["c"]

        c = MagicMock(spec=ModuleDescriptor)
        c.name = "c"
        c.dependencies = []

        result = resolve_dependencies([a, b, c])

        # c -> b -> a
        names = [m.name for m in result]
        assert names.index("c") < names.index("b")
        assert names.index("b") < names.index("a")

    def test_cyclic_dependency_raises_error(self):
        """测试循环依赖抛出异常"""
        a = MagicMock(spec=ModuleDescriptor)
        a.name = "a"
        a.dependencies = ["b"]

        b = MagicMock(spec=ModuleDescriptor)
        b.name = "b"
        b.dependencies = ["a"]

        with pytest.raises(CyclicDependencyError):
            resolve_dependencies([a, b])

    def test_missing_dependency_raises_error(self):
        """测试缺少依赖抛出异常"""
        module = MagicMock(spec=ModuleDescriptor)
        module.name = "test"
        module.dependencies = ["nonexistent"]

        with pytest.raises(ValueError, match="not available"):
            resolve_dependencies([module])


class TestFilterModules:
    """模块过滤测试"""

    def test_filter_none_returns_all(self):
        """测试不传过滤参数返回全部"""
        module1 = MagicMock(spec=ModuleDescriptor)
        module1.name = "module1"
        module2 = MagicMock(spec=ModuleDescriptor)
        module2.name = "module2"

        result = filter_modules([module1, module2], None)

        assert len(result) == 2

    def test_filter_by_names(self):
        """测试按名称过滤"""
        module1 = MagicMock(spec=ModuleDescriptor)
        module1.name = "module1"
        module2 = MagicMock(spec=ModuleDescriptor)
        module2.name = "module2"
        module3 = MagicMock(spec=ModuleDescriptor)
        module3.name = "module3"

        result = filter_modules([module1, module2, module3], ["module1", "module3"])

        assert len(result) == 2
        names = [m.name for m in result]
        assert "module1" in names
        assert "module3" in names
        assert "module2" not in names

    def test_filter_nonexistent_raises_error(self):
        """测试过滤不存在的模块抛出异常"""
        module = MagicMock(spec=ModuleDescriptor)
        module.name = "test"

        with pytest.raises(ValueError, match="not found"):
            filter_modules([module], ["nonexistent"])
