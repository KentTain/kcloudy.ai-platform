"""
GraphRAG 组件导入测试

验证迁移后的模块可以正确导入。

注意：此测试需要使用 PYTHONPATH=src 运行，或者确保项目已安装。
测试直接导入 graphrag 子模块，避免 ai.components.__init__.py 中的其他组件依赖。
"""

import sys
import importlib

import pytest


class TestGraphRAGImports:
    """GraphRAG 组件导入测试"""

    def test_import_config_enums(self):
        """测试导入 config.enums"""
        # 直接导入，不经过 ai.components.__init__
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "graphrag_config_enums",
            "src/ai/components/graphrag/config/enums.py",
        )
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(module, "CacheType")
        assert hasattr(module, "StorageType")

    def test_import_config_defaults(self):
        """测试导入 config.defaults（需要 datashaper 可选依赖）"""
        # datashaper 是 graphrag 可选依赖组的依赖，未安装时自动跳过
        pytest.importorskip("datashaper")

        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "graphrag_config_defaults",
            "src/ai/components/graphrag/config/defaults.py",
        )
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 验证默认值模块加载成功
        assert module is not None


class TestGraphRAGSyntax:
    """GraphRAG 语法验证测试"""

    def test_all_python_files_have_valid_syntax(self):
        """验证所有 Python 文件语法有效"""
        import ast
        from pathlib import Path

        graphrag_dir = Path("src/ai/components/graphrag")
        syntax_errors = []

        for py_file in graphrag_dir.rglob("*.py"):
            try:
                with open(py_file, encoding="utf-8") as f:
                    source = f.read()
                ast.parse(source)
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}: {e}")

        assert not syntax_errors, f"发现语法错误:\n" + "\n".join(syntax_errors)

    def test_no_alon_imports_remaining(self):
        """验证没有遗留的 alon 导入"""
        from pathlib import Path

        graphrag_dir = Path("src/ai/components/graphrag")
        alon_imports = []

        for py_file in graphrag_dir.rglob("*.py"):
            with open(py_file, encoding="utf-8") as f:
                content = f.read()
            if "alon." in content or "from alon" in content or "import alon" in content:
                alon_imports.append(str(py_file))

        assert not alon_imports, f"发现遗留的 alon 导入:\n" + "\n".join(alon_imports)
