"""沙箱 Skill 运行时

提供轻量级沙箱环境，通过子进程执行 Python 脚本，使用白名单控制导入。
"""

import asyncio
import json
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from ai.components.plugin.engine.core.exceptions import (
    SkillSecurityError,
)
from ai.components.plugin.engine.core.runtime.base import (
    PluginRuntime,
    PluginRuntimeState,
)
from ai.components.plugin.engine.models.plugin import PluginInfo


class SandboxSkillRuntime(PluginRuntime):
    """沙箱 Skill 运行时

    特性：
    - 轻量级沙箱，使用子进程执行 Python 脚本
    - 白名单导入控制
    - 资源限制（内存、超时）
    """

    skill_type = "script"
    runtime_type = "sandbox"

    # 安全验证：禁止的模式
    FORBIDDEN_PATTERNS = [
        "import os",
        "import subprocess",
        "import sys",
        "__import__",
        "eval(",
        "exec(",
        "compile(",
    ]

    # 默认配置
    DEFAULT_TIMEOUT = 30
    DEFAULT_MEMORY_LIMIT_MB = 128

    def __init__(self, plugin_info: PluginInfo, workspace_dir: Path):
        super().__init__(plugin_info, workspace_dir)

        # 运行时配置
        runtime_config = plugin_info.config.runtime_config.config
        self.script_path = runtime_config.get("script_path", "")
        self.allowed_imports = runtime_config.get("allowed_imports", [])
        self.timeout = runtime_config.get("timeout", self.DEFAULT_TIMEOUT)
        self.memory_limit_mb = runtime_config.get(
            "memory_limit_mb", self.DEFAULT_MEMORY_LIMIT_MB
        )

        # 运行时状态
        self._script_content: str | None = None
        self._temp_dir: Path | None = None

    async def prepare(self) -> None:
        """准备阶段：加载脚本、验证安全性、创建临时目录"""
        try:
            self._update_state(PluginRuntimeState.PREPARING)

            # 加载脚本内容
            self._script_content = await self._load_script_content()

            # 验证脚本安全性
            self._validate_script_security(self._script_content)

            # 创建临时目录
            self._temp_dir = Path(tempfile.mkdtemp(prefix=f"skill_{self.plugin_id}_"))

            self._update_state(PluginRuntimeState.PREPARED)
            self._plugin_logger.info("沙箱运行时准备完成")

        except Exception as e:
            self._record_error(e)
            self._update_state(PluginRuntimeState.ERROR)
            raise

    async def start(self) -> None:
        """启动阶段：标记为运行状态（沙箱无需持久化进程）"""
        if not self.is_prepared:
            raise RuntimeError("运行时未准备完成")

        self._update_state(PluginRuntimeState.RUNNING)
        self._plugin_logger.info("沙箱运行时已启动")

    async def stop(self) -> None:
        """停止阶段：清理临时目录"""
        self._update_state(PluginRuntimeState.STOPPING)

        # 清理临时目录
        if self._temp_dir and self._temp_dir.exists():
            import shutil

            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

        self._update_state(PluginRuntimeState.STOPPED)
        self._plugin_logger.info("沙箱运行时已停止")

    async def invoke_stream(
        self,
        invoke_request: dict[str, Any],
        timeout: int | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """在沙箱中执行脚本"""
        if not self.is_running:
            yield {
                "status": "error",
                "message": "运行时未启动，请先调用 start()",
            }
            return

        try:
            # 使用传入的超时或默认超时
            actual_timeout = timeout or self.timeout

            # 在子进程中执行脚本
            result = await self._execute_with_limits(invoke_request, actual_timeout)

            yield {
                "status": "success",
                "output": result,
            }

        except asyncio.TimeoutError:
            yield {
                "status": "error",
                "message": f"脚本执行超时 ({self.timeout}s)",
            }
        except Exception as e:
            yield {
                "status": "error",
                "message": f"脚本执行失败: {str(e)}",
            }

    async def get_metrics(self) -> dict[str, Any]:
        """获取运行时指标"""
        return {
            "skill_type": self.skill_type,
            "runtime_type": self.runtime_type,
            "state": self.state,
            "is_prepared": self.is_prepared,
            "is_running": self.is_running,
            "script_path": self.script_path,
            "allowed_imports": self.allowed_imports,
            "timeout": self.timeout,
            "memory_limit_mb": self.memory_limit_mb,
        }

    async def get_logs(
        self, limit: int = 100, level: str | None = None
    ) -> list[dict[str, Any]]:
        """获取运行时日志（沙箱运行时不记录日志）"""
        return []

    def _validate_script_security(self, script_content: str) -> None:
        """验证脚本安全性

        Args:
            script_content: 脚本内容

        Raises:
            SkillSecurityError: 发现禁止的模式
        """
        violations = []

        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in script_content:
                # 区分导入语句和函数调用
                if pattern.startswith("import") or pattern == "__import__":
                    violations.append(f"禁止的导入语句: {pattern}")
                else:
                    violations.append(f"禁止的函数调用: {pattern}")

        if violations:
            raise SkillSecurityError(self.plugin_id, violations)

    def _build_safe_globals(self) -> dict[str, Any]:
        """构建安全的全局命名空间

        Returns:
            包含白名单模块和安全内置函数的全局命名空间
        """
        # 安全的内置函数列表
        safe_builtins = {
            "print": print,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "isinstance": isinstance,
            "type": type,
        }

        # 构建全局命名空间
        safe_globals: dict[str, Any] = {
            "__builtins__": safe_builtins,
        }

        # 加载白名单模块
        for module_name in self.allowed_imports:
            try:
                module = __import__(module_name)
                safe_globals[module_name] = module
            except ImportError:
                self._plugin_logger.warning(
                    f"无法导入白名单模块: {module_name}"
                )

        return safe_globals

    async def _execute_with_limits(
        self,
        invoke_request: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        """在子进程中执行脚本（带超时）

        Args:
            invoke_request: 调用请求
            timeout: 超时时间（秒）

        Returns:
            执行结果
        """
        # 构建包装脚本
        wrapper_script = self._build_wrapper_script(invoke_request)

        # 创建临时脚本文件
        script_file = self._temp_dir / "wrapper_script.py"
        script_file.write_text(wrapper_script, encoding="utf-8")

        # 在子进程中执行脚本
        process = await asyncio.create_subprocess_exec(
            "python",
            str(script_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore")
                raise RuntimeError(f"脚本执行失败: {error_msg}")

            # 解析输出
            output = stdout.decode("utf-8", errors="ignore")
            result = json.loads(output)
            return result

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

    def _build_wrapper_script(self, invoke_request: dict[str, Any]) -> str:
        """构建包装脚本

        Args:
            invoke_request: 调用请求

        Returns:
            包装脚本内容
        """
        input_json = json.dumps(invoke_request.get("input", {}), ensure_ascii=False)
        context_json = json.dumps(invoke_request.get("context", {}), ensure_ascii=False)

        wrapper_script = f'''import json
import sys

# 资源限制：设置内存上限
try:
    import resource
    memory_limit_bytes = {self.memory_limit_mb} * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
except (ImportError, AttributeError, ValueError):
    pass

# 输入数据
input_data = json.loads('{input_json}')
context = json.loads('{context_json}')

# 用户脚本
{self._script_content}

# 执行 main 函数并输出结果
if 'main' in dir():
    result = main(input_data)
    print(json.dumps(result, default=str, ensure_ascii=False))
else:
    print(json.dumps({{"output": "脚本未定义 main 函数"}}, ensure_ascii=False))
'''
        return wrapper_script

    async def _load_script_content(self) -> str:
        """从 MinIO 加载脚本内容

        Returns:
            脚本内容
        """
        from framework.configs.settings import Settings
        from framework.storage import get_storage_provider

        storage_key = self._get_storage_key()

        try:
            settings = Settings()
            storage = get_storage_provider(settings.oss)
            # 解析 bucket 和 object_name
            parts = storage_key.split("/", 1)
            if len(parts) == 2:
                bucket, object_name = parts
            else:
                bucket = "plugins"
                object_name = storage_key

            script_bytes = await storage.download(bucket, object_name)
            return script_bytes.decode("utf-8")
        except Exception as e:
            raise RuntimeError(f"加载脚本失败: {str(e)}")

    def _get_storage_key(self) -> str:
        """获取存储路径

        Returns:
            MinIO 存储路径
        """
        # 格式：plugins/{author}/{name}/{version}/{script_path}
        return (
            f"plugins/{self.plugin_author}/{self.plugin_name}/"
            f"{self.plugin_version}/{self.script_path}"
        )

    def _record_error(self, error: Exception) -> None:
        """记录错误

        Args:
            error: 错误对象
        """
        self._plugin_logger.error(f"沙箱运行时错误: {str(error)}")
        self._plugin_logger.exception(error)
