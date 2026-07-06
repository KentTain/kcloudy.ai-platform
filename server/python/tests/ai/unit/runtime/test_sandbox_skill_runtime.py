"""SandboxSkillRuntime 单元测试

测试沙箱运行时的安全验证、全局命名空间构建和执行功能。
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 直接导入需要的模块，避免通过 ai.components 导入（会触发 datasource 的 langchain_community 依赖）
from ai.components.plugin.engine.core.exceptions import (
    SkillPreparationError,
    SkillSecurityError,
)
from ai.components.plugin.engine.core.runtime.sandbox_skill_runtime import (
    SandboxSkillRuntime,
)
from ai.components.plugin.engine.models.plugin import PluginInfo


@pytest.fixture
def mock_plugin_info() -> MagicMock:
    """创建模拟的插件信息"""
    plugin_info = MagicMock(spec=PluginInfo)
    plugin_info.config = MagicMock()
    plugin_info.config.configuration = MagicMock()
    plugin_info.config.configuration.author = "test-author"
    plugin_info.config.configuration.name = "test-skill"
    plugin_info.config.configuration.version = "1.0.0"
    plugin_info.config.runtime_config = MagicMock()
    plugin_info.config.runtime_config.skill_type = "script"
    plugin_info.config.runtime_config.config = {
        "script_path": "skills/test.py",
        "allowed_imports": ["json", "math"],
        "timeout": 30,
        "memory_limit_mb": 128,
    }
    return plugin_info


@pytest.fixture
def workspace_dir(tmp_path: Path) -> Path:
    """创建临时工作目录"""
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


class TestSandboxSkillRuntime:
    """SandboxSkillRuntime 测试类"""

    def test_runtime_type(self, mock_plugin_info: MagicMock, workspace_dir: Path):
        """测试运行时类型属性"""
        runtime = SandboxSkillRuntime(mock_plugin_info, workspace_dir)

        assert runtime.skill_type == "script"
        assert runtime.runtime_type == "sandbox"

    def test_validate_script_with_forbidden_import_os(
        self, mock_plugin_info: MagicMock, workspace_dir: Path
    ):
        """测试验证脚本时检测到禁止导入 os"""
        runtime = SandboxSkillRuntime(mock_plugin_info, workspace_dir)

        forbidden_script = """
import os

def main(input_data):
    return {"result": input_data}
"""

        with pytest.raises(SkillSecurityError) as exc_info:
            runtime._validate_script_security(forbidden_script)

        assert "禁止的导入语句: import os" in str(exc_info.value)

    def test_validate_script_with_forbidden_subprocess(
        self, mock_plugin_info: MagicMock, workspace_dir: Path
    ):
        """测试验证脚本时检测到禁止导入 subprocess"""
        runtime = SandboxSkillRuntime(mock_plugin_info, workspace_dir)

        forbidden_script = """
import subprocess

def main(input_data):
    return {"result": input_data}
"""

        with pytest.raises(SkillSecurityError) as exc_info:
            runtime._validate_script_security(forbidden_script)

        assert "禁止的导入语句: import subprocess" in str(exc_info.value)

    def test_validate_script_with_eval(
        self, mock_plugin_info: MagicMock, workspace_dir: Path
    ):
        """测试验证脚本时检测到禁止使用 eval"""
        runtime = SandboxSkillRuntime(mock_plugin_info, workspace_dir)

        forbidden_script = """
def main(input_data):
    result = eval(input_data["code"])
    return {"result": result}
"""

        with pytest.raises(SkillSecurityError) as exc_info:
            runtime._validate_script_security(forbidden_script)

        assert "禁止的函数调用: eval(" in str(exc_info.value)

    def test_validate_safe_script(
        self, mock_plugin_info: MagicMock, workspace_dir: Path
    ):
        """测试安全脚本通过验证"""
        runtime = SandboxSkillRuntime(mock_plugin_info, workspace_dir)

        safe_script = """
import json
import math

def main(input_data):
    result = math.sqrt(input_data["value"])
    return {"result": result}
"""

        # 不应该抛出异常
        runtime._validate_script_security(safe_script)

    def test_build_safe_globals_only_allows_whitelist(
        self, mock_plugin_info: MagicMock, workspace_dir: Path
    ):
        """测试安全全局命名空间仅包含白名单模块"""
        runtime = SandboxSkillRuntime(mock_plugin_info, workspace_dir)

        # 模拟导入
        with patch.dict("sys.modules", {"json": MagicMock(), "math": MagicMock()}):
            safe_globals = runtime._build_safe_globals()

            # 应该包含白名单模块
            assert "json" in safe_globals
            assert "math" in safe_globals

            # 不应该包含危险模块
            assert "os" not in safe_globals
            assert "subprocess" not in safe_globals
            assert "sys" not in safe_globals

    def test_build_safe_globals_includes_basic_builtins(
        self, mock_plugin_info: MagicMock, workspace_dir: Path
    ):
        """测试安全全局命名空间包含基础内置函数"""
        runtime = SandboxSkillRuntime(mock_plugin_info, workspace_dir)

        safe_globals = runtime._build_safe_globals()

        # 检查 __builtins__ 是否包含允许的函数
        builtins = safe_globals["__builtins__"]
        allowed_functions = [
            "print",
            "len",
            "str",
            "int",
            "float",
            "bool",
            "list",
            "dict",
            "tuple",
            "set",
            "range",
            "enumerate",
            "zip",
            "map",
            "filter",
            "sorted",
            "reversed",
            "sum",
            "min",
            "max",
            "abs",
            "round",
            "isinstance",
            "type",
        ]

        for func_name in allowed_functions:
            assert func_name in builtins, f"缺少内置函数: {func_name}"

        # 检查危险函数是否被排除
        forbidden_functions = ["eval", "exec", "compile", "__import__", "open"]
        for func_name in forbidden_functions:
            assert func_name not in builtins, f"禁止的函数不应存在: {func_name}"

    @pytest.mark.asyncio
    async def test_invoke_stream_not_running(
        self, mock_plugin_info: MagicMock, workspace_dir: Path
    ):
        """测试未运行时调用 invoke_stream 返回错误"""
        runtime = SandboxSkillRuntime(mock_plugin_info, workspace_dir)

        invoke_request = {"input": {"value": 42}}

        # 未调用 start，is_running = False
        results = []
        async for result in runtime.invoke_stream(invoke_request):
            results.append(result)

        # 应该返回一个错误结果
        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert "未启动" in results[0]["message"]

    @pytest.mark.asyncio
    async def test_get_metrics(
        self, mock_plugin_info: MagicMock, workspace_dir: Path
    ):
        """测试获取运行时指标"""
        runtime = SandboxSkillRuntime(mock_plugin_info, workspace_dir)

        metrics = await runtime.get_metrics()

        assert "skill_type" in metrics
        assert "runtime_type" in metrics
        assert "state" in metrics
        assert metrics["skill_type"] == "script"
        assert metrics["runtime_type"] == "sandbox"
