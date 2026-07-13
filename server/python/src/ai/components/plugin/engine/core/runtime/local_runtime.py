"""
本地插件运行时
分离重量级预处理和轻量级启动
通过子进程运行插件，使用JSON通信协议，支持Python虚拟环境隔离
"""

import asyncio
import json
import os
import platform
import shutil
import time
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any, override

import psutil

from ai.components.plugin.engine.core.communication.protocol import (
    PluginCommunicationError,
    PluginError,
    PluginMessageProtocol,
    PluginTimeoutError,
)
from ai.components.plugin.engine.models.plugin import PluginInfo
from ai.components.plugin.engine.utils.helpers import find_available_port
from ai_plugin.server.core.server.__base.writer_entities import Event
from framework.configs.settings import get_settings

from .base import PluginRuntime, PluginRuntimeState


class PluginPermissions:
    """插件权限管理"""

    def __init__(self, permissions):
        # 处理字典或Pydantic模型
        if hasattr(permissions, "__dict__"):
            # Pydantic模型
            self.network_access = getattr(permissions, "network_access", False)
            self.file_system_access = getattr(permissions, "file_system_access", [])
            self.env_vars_access = getattr(permissions, "env_vars_access", [])
            self.subprocess_access = getattr(permissions, "subprocess_access", False)
            self.internet_hosts = getattr(permissions, "internet_hosts", [])
            self.local_ports = getattr(permissions, "local_ports", [])
        else:
            # 字典
            self.network_access = (
                permissions.get("network_access", False) if permissions else False
            )
            self.file_system_access = (
                permissions.get("file_system_access", []) if permissions else []
            )
            self.env_vars_access = (
                permissions.get("env_vars_access", []) if permissions else []
            )
            self.subprocess_access = (
                permissions.get("subprocess_access", False) if permissions else False
            )
            self.internet_hosts = (
                permissions.get("internet_hosts", []) if permissions else []
            )
            self.local_ports = permissions.get("local_ports", []) if permissions else []

    def can_access_network(self) -> bool:
        """是否可以访问网络"""
        return self.network_access

    def can_access_path(self, path: str) -> bool:
        """是否可以访问指定路径"""
        if not self.file_system_access:
            return False

        path = os.path.normpath(path)
        return any(
            path.startswith(allowed_path) for allowed_path in self.file_system_access
        )

    def can_access_host(self, host: str) -> bool:
        """是否可以访问指定主机"""
        if not self.network_access:
            return False

        if "*" in self.internet_hosts:
            return True

        return host in self.internet_hosts

    def can_use_subprocess(self) -> bool:
        """是否可以使用子进程"""
        return self.subprocess_access


class LocalPluginRuntime(PluginRuntime):
    """本地插件运行时"""

    def __init__(self, plugin_info: PluginInfo, workspace_dir: Path):
        super().__init__(plugin_info, workspace_dir=workspace_dir)

        # 预处理相关状态
        self.virtual_env_path: Path | None = None
        self.python_interpreter_path: str | None = None
        self.uv_path: str | None = None
        self.environment_info: dict[str, Any] = {}

        # 运行时相关状态
        self.process: asyncio.subprocess.Process | None = None
        self.log_file: Path = self.workspace_dir / "plugin.log"
        self._communication_lock = asyncio.Lock()
        self._output_task: asyncio.Task | None = None

        # 权限管理
        # 兼容处理：plugin_config 可能是 dict 或对象
        configuration = None
        if isinstance(self.plugin_config, dict):
            configuration = self.plugin_config.get('configuration', {})
        elif hasattr(self.plugin_config, 'configuration'):
            configuration = self.plugin_config.configuration
        else:
            configuration = {}

        # 获取 resource 配置
        resource = None
        if isinstance(configuration, dict):
            resource = configuration.get('resource', {})
        elif hasattr(configuration, 'resource'):
            resource = configuration.resource
        else:
            resource = {}

        # 获取 permission 配置
        permission = None
        if isinstance(resource, dict):
            permission = resource.get('permission', {})
        elif hasattr(resource, 'permission'):
            permission = resource.permission
        else:
            permission = {}

        self.permissions = PluginPermissions(permission)

        # 预处理状态标记文件
        self._prepared_marker_file: Path | None = None

        # 并发响应管理
        self._pending_requests: dict[str, asyncio.Future] = {}  # session_id -> Future
        self._streaming_requests: dict[
            str, asyncio.Queue
        ] = {}  # session_id -> Queue (用于流式响应)
        self._streaming_start_time: dict[
            str, float
        ] = {}  # session_id -> 开始时间（用于计算耗时）
        self._response_reader_task: asyncio.Task | None = None

        # 插件就绪状态标志
        self._plugin_ready = False
        self._plugin_metadata_received = False
        self._plugin_heartbeat_received = False

        # 心跳日志时间控制
        self._last_heartbeat_log_time: datetime | None = None

        # 设置工作目录
        self.set_workspace_dir(workspace_dir)

    @override
    def set_workspace_dir(self, workspace_dir: Path):
        """设置工作目录"""
        super().set_workspace_dir(workspace_dir)

        # 设置预处理状态标记文件
        self._prepared_marker_file = workspace_dir / ".prepared"

        # 检查是否已完成预处理
        if self._prepared_marker_file and self._prepared_marker_file.exists():
            # 检查self.plugin_version跟之前预处理的plugin_version是否一致
            with open(self._prepared_marker_file, encoding="utf-8") as f:
                prepared_info = f.read().splitlines()
                for line in prepared_info:
                    if line.startswith("plugin_version:"):
                        prepared_plugin_version = line.split(":")[1].strip()
                        break
                else:
                    prepared_plugin_version = None

                if prepared_plugin_version != self.plugin_version:
                    self._plugin_logger.warning(
                        f"插件 {self.plugin_name} 版本不一致，旧版本: {prepared_plugin_version}，新版本: {self.plugin_version}",
                    )
                    self._prepared_marker_file.unlink()
                    self._is_prepared = False
                else:
                    self._is_prepared = True
                    self._plugin_logger.info(
                        f"插件 {self.plugin_name} 检测到预处理标记文件，已完成预处理"
                    )
        else:
            self._is_prepared = False
            self._plugin_logger.info(
                f"插件 {self.plugin_name} 未检测到预处理标记文件，未完成预处理"
            )

    @override
    async def prepare(self) -> None:
        """
        安装时重量级预处理
        包括：Python环境检查、UV检查、环境创建、文件解压、依赖安装、预编译、安全扫描
        """
        if self.is_prepared:
            self._plugin_logger.info(f"插件 {self.plugin_name} 已完成预处理，跳过")
            return

        self._plugin_logger.info(f"开始预处理插件: {self.plugin_name}")
        self._update_state(PluginRuntimeState.PREPARING)

        try:
            # 1. 检查UV工具可用性
            await self._check_uv_available()

            # 2. 📁 准备工作目录结构
            await self._prepare_workspace_structure()

            # 3. 📂 解压和组织插件文件
            await self._extract_plugin_files()

            # 4.  深度安全扫描
            await self._deep_security_scan()

            # 5. 🐍 初始化Python虚拟环境
            await self._initialize_virtual_environment()

            # 6.  安装所有依赖包
            await self._install_dependencies()

            # 7.  预编译Python文件
            await self._precompile_python_files()

            # 9.  生成运行时清单
            await self._generate_runtime_manifest()

            # 10.  预分配资源配置
            await self._preconfigure_resources()

            # 创建预处理完成标记文件
            if self._prepared_marker_file:
                with open(self._prepared_marker_file, "w", encoding="utf-8") as f:
                    f.write(f"prepared_at: {datetime.now().isoformat()}\n")
                    f.write(f"plugin_name: {self.plugin_name}\n")
                    f.write(f"plugin_version: {self.plugin_version}\n")

            self._update_state(PluginRuntimeState.PREPARED)
            self._plugin_logger.info(f"插件 {self.plugin_name} 预处理完成")

        except Exception as e:
            self._update_state(PluginRuntimeState.ERROR)
            self._plugin_logger.error(f"插件 {self.plugin_name} 预处理失败: {e}")
            raise RuntimeError(f"预处理失败: {e}")

    async def start(self) -> None:
        """
        轻量级快速启动
        前提：已经完成prepare()
        """
        if self.is_running:
            self._plugin_logger.info(f"插件 {self.plugin_name} 已在运行")
            return

        if not self.is_prepared:
            raise RuntimeError(
                f"插件 {self.plugin_name} 未完成预处理，请先调用prepare()"
            )

        self._plugin_logger.info(f"快速启动插件: {self.plugin_name}")
        self._update_state(PluginRuntimeState.STARTING)

        # 重置就绪状态标志
        self._plugin_ready = False
        self._plugin_metadata_received = False
        self._plugin_heartbeat_received = False

        try:
            # 1.  查找可用端口
            self.port = find_available_port()
            if not self.port:
                raise RuntimeError("无法找到可用端口")

            # 1.5. 🐍 确保Python解释器路径已设置（跳过预处理时需要）
            if not self.python_interpreter_path or not self.virtual_env_path:
                # 设置虚拟环境路径
                if not self.virtual_env_path:
                    self.virtual_env_path = self.workspace_dir / ".venv"
                await self._setup_python_interpreter_path()

            # 2.  启动插件进程
            await self._start_plugin_process()

            # 3.  等待插件就绪
            await self._wait_for_plugin_ready()

            # 4.  注册监控
            await self._register_monitoring()

            # 5.  设置进程安全限制
            await self._setup_runtime_security()

            self._update_state(PluginRuntimeState.RUNNING)
            self._plugin_logger.info(
                f"插件 {self.plugin_name} 启动成功，PID: {self.process_id}"
            )

        except Exception as e:
            self._update_state(PluginRuntimeState.ERROR)
            await self._cleanup_on_start_failure()
            self._plugin_logger.error(f"启动插件 {self.plugin_name} 失败: {e}")
            raise RuntimeError(f"启动失败: {e}")

    async def stop(self) -> None:
        """停止插件"""
        if not self.is_running:
            return

        self._plugin_logger.info(f"停止插件: {self.plugin_name}")
        self._update_state(PluginRuntimeState.STOPPING)

        try:
            await self._cleanup()
        except Exception as e:
            self._plugin_logger.warning(f"清理插件 {self.plugin_name} 失败: {e}")

        try:
            if self.process and self.process.returncode is None:
                # 等待进程结束
                try:
                    # 优雅停止
                    self.process.terminate()
                    await asyncio.wait_for(self.process.wait(), timeout=10)
                except Exception as e:
                    # 强制杀死进程
                    self._plugin_logger.warning(
                        f"插件 {self.plugin_name} 未能优雅停止，强制终止, {e}"
                    )
                    self.process.kill()
                    await self.process.wait()

            self._update_state(PluginRuntimeState.STOPPED)
            self._plugin_logger.info(f"插件 {self.plugin_name} 已停止")

        except Exception as e:
            self._plugin_logger.error(f"停止插件 {self.plugin_name} 失败: {e}")
            raise
        finally:
            self.process = None
            self.process_id = None
            self.port = None

    async def invoke_stream(
        self,
        invoke_request: dict[str, Any],
        timeout: int,
        session_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """流式调用插件方法"""
        if not self.is_running:
            raise RuntimeError(f"插件 {self.plugin_name} 未运行")

        action = invoke_request.get("action")
        self._plugin_logger.debug(f"开始流式调用插件方法: {self.plugin_name}.{action}")

        try:
            # 使用流式发送消息
            async for chunk in self._send_message_stream(
                invoke_request, timeout, session_id
            ):
                # self._plugin_logger.debug(f"收到流式数据: {str(chunk)[:400]}...")
                yield chunk

        except Exception as e:
            self._plugin_logger.error(
                f"流式调用插件 {self.plugin_name} 方法 {action} 失败: {e}"
            )
            raise e

    async def get_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        if not self.is_running or not self.process:
            return {}

        try:
            # 获取进程信息
            process = psutil.Process(self.process.pid)

            # CPU和内存使用率
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            # 运行时间
            uptime = (
                (datetime.now() - self.started_at).total_seconds()
                if self.started_at
                else 0
            )

            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory_info.rss / 1024 / 1024,  # MB
                "memory_percent": memory_percent,
                "uptime": uptime,
                "last_updated": datetime.now(),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self._plugin_logger.warning(f"获取插件 {self.plugin_name} 指标失败: {e}")
            return {}

    async def get_logs(
        self, limit: int = 100, level: str | None = None
    ) -> list[dict[str, Any]]:
        """获取插件日志"""
        logs = []

        if not self.log_file or not self.log_file.exists():
            return logs

        try:
            with open(self.log_file, encoding="utf-8") as f:
                lines = f.readlines()

                # 取最后limit行
                recent_lines = lines[-limit:] if len(lines) > limit else lines

                for line in recent_lines:
                    line = line.strip()
                    if not line:
                        continue

                    # 简单的日志解析
                    try:
                        log_data = json.loads(line)
                        if level and log_data.get("level", "").lower() != level.lower():
                            continue
                        logs.append(log_data)
                    except json.JSONDecodeError:
                        # 如果不是JSON格式，创建简单的日志条目
                        logs.append(
                            {
                                "timestamp": datetime.now().isoformat(),
                                "level": "INFO",
                                "message": line,
                                "source": self.plugin_name,
                            },
                        )
        except Exception as e:
            self._plugin_logger.error(f"读取插件 {self.plugin_name} 日志失败: {e}")

        return logs

    async def _cleanup(self):
        """清理资源"""
        # 停止响应读取器
        if self._response_reader_task and not self._response_reader_task.done():
            self._response_reader_task.cancel()
            try:
                await self._response_reader_task
            except asyncio.CancelledError:
                self._plugin_logger.warning(
                    f"响应读取器已取消: {self._response_reader_task}"
                )

        # 清理普通请求
        for session_id, future in self._pending_requests.items():
            if not future.done():
                future.set_exception(PluginError("插件进程已停止"))
        self._pending_requests.clear()

        # 清理流式请求
        for session_id, queue in self._streaming_requests.items():
            try:
                await queue.put(Exception("插件进程已停止"))
            except:
                self._plugin_logger.warning(f"流式请求队列已关闭: {session_id}")
        self._streaming_requests.clear()

        if self._output_task and not self._output_task.done():
            self._output_task.cancel()

    # ==================== 预处理方法（重量级操作）====================

    async def _check_uv_available(self) -> None:
        """1. 检查UV工具可用性"""
        self._plugin_logger.info(f"检查UV工具可用性: {self.plugin_name}")

        # 尝试多种方式找到UV
        uv_candidates = []

        # 1. 尝试从配置获取
        try:
            settings = get_settings()
            if settings.plugin.uv_path:
                uv_candidates.append(settings.plugin.uv_path)
                self._plugin_logger.debug(f"从配置获取 uv_path: {settings.plugin.uv_path}")
        except RuntimeError:
            # 配置未初始化，跳过
            self._plugin_logger.debug("配置未初始化")

        # 2. 尝试从环境变量获取
        uv_path_env = os.environ.get("UV_PATH")
        if uv_path_env:
            uv_candidates.append(uv_path_env)
            self._plugin_logger.debug(f"从环境变量获取 UV_PATH: {uv_path_env}")

        # 3. 使用 shutil.which 查找
        which_result = shutil.which("uv")
        if which_result:
            uv_candidates.append(which_result)
            self._plugin_logger.debug(f"从 shutil.which 获取: {which_result}")

        # 4. 添加常见路径作为备选
        home = Path.home()
        common_uv_paths = [
            home / ".local" / "bin" / "uv.exe",  # Windows
            home / ".local" / "bin" / "uv",  # Linux/Mac
            Path("C:/Users") / os.environ.get("USERNAME", "") / ".local" / "bin" / "uv.exe",  # Windows 备选
        ]
        for common_path in common_uv_paths:
            if common_path.exists():
                uv_candidates.append(str(common_path))
                self._plugin_logger.debug(f"从常见路径获取: {common_path}")

        self._plugin_logger.info(f"UV 候选路径: {uv_candidates}")

        for candidate in uv_candidates:
            if candidate and Path(candidate).exists():
                # 验证UV版本
                try:
                    self._plugin_logger.debug(f"正在验证 UV: {candidate}")
                    process = await asyncio.create_subprocess_exec(
                        candidate,
                        "--version",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await process.communicate()

                    if process.returncode == 0:
                        uv_version = stdout.decode().strip()
                        self.uv_path = candidate
                        self.environment_info["uv_path"] = candidate
                        self.environment_info["uv_version"] = uv_version
                        self._plugin_logger.info(
                            f"找到UV: {candidate}, 版本: {uv_version}"
                        )
                        return
                    else:
                        stderr_text = stderr.decode().strip() if stderr else ""
                        self._plugin_logger.warning(
                            f"UV 版本检查失败: {candidate}, returncode={process.returncode}, stderr={stderr_text}"
                        )
                except BaseException as e:
                    import traceback
                    self._plugin_logger.warning(
                        f"检查 UV 候选路径失败: {candidate}, 异常类型={type(e).__name__}, 错误={e}"
                    )
                    self._plugin_logger.debug(f"异常堆栈:\n{traceback.format_exc()}")
                    continue

        raise RuntimeError("未找到uv，请先安装uv")

    async def _prepare_workspace_structure(self) -> None:
        """2. 📁 准备完整工作目录结构"""
        # self._plugin_logger.info(f"准备工作目录结构: {self.plugin_name}")

        if not self.workspace_dir:
            raise RuntimeError("工作目录未设置")

        # 创建标准目录结构
        directories = [
            self.workspace_dir,
            self.workspace_dir / "logs",
            self.workspace_dir / "config",
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                # self._plugin_logger.debug(f"创建目录: {directory}")
            except Exception as e:
                self._plugin_logger.error(f"创建目录失败 {directory}: {e}")
                raise RuntimeError(f"创建目录失败 {directory}: {e}")

        self._plugin_logger.info(f"工作目录结构准备完成: {self.workspace_dir}")

    async def _extract_plugin_files(self) -> None:
        """3. 📂 解压和组织插件文件"""
        self._plugin_logger.info(f"解压插件文件: {self.plugin_name}")

    async def _deep_security_scan(self) -> None:
        """4.  深度安全扫描"""
        self._plugin_logger.info(f"进行深度安全扫描: {self.plugin_name}")

        # 检查workspace_dir是否为None
        if not self.workspace_dir:
            raise RuntimeError("工作目录未设置，无法创建虚拟环境")

        # 扫描所有Python文件，但排除虚拟环境目录
        scan_results = []
        for py_file in self.workspace_dir.rglob("*.py"):
            # 跳过虚拟环境目录
            if ".venv" in py_file.parts or "__pycache__" in py_file.parts:
                continue

            try:
                code_content = py_file.read_text(encoding="utf-8")

                # 检查恶意代码模式（简化版安全扫描）
                malicious_patterns = self._scan_malicious_patterns(code_content)
                if malicious_patterns:
                    scan_results.append(
                        {
                            "file": str(py_file.relative_to(self.workspace_dir)),
                            "patterns": malicious_patterns,
                            "severity": "high"
                            if any(
                                "eval" in p or "exec" in p for p in malicious_patterns
                            )
                            else "medium",
                        },
                    )

            except Exception as e:
                self._plugin_logger.error(f"扫描文件 {py_file} 失败: {e}")

        # 记录扫描结果
        self.environment_info["security_scan"] = {
            "scanned_files": len(list(self.workspace_dir.rglob("*.py"))),
            "issues_found": len(scan_results),
            "scan_results": scan_results,
            "scan_time": datetime.now().isoformat(),
        }

        # 如果启用了严格模式且发现高风险模式，则拒绝
        high_risk_issues = [r for r in scan_results if r["severity"] == "high"]
        if get_settings().plugin.strict_security_mode and high_risk_issues:
            raise RuntimeError(f"插件包含高风险代码，拒绝安装: {high_risk_issues}")

        if scan_results:
            self._plugin_logger.warning(
                f"安全扫描发现 {len(scan_results)} 个潜在问题: {scan_results}"
            )
        else:
            self._plugin_logger.info("安全扫描通过，未发现问题")

    def _scan_malicious_patterns(self, code_content: str) -> list[str]:
        """简化版恶意代码模式扫描"""
        patterns = []
        dangerous_functions = [
            "eval(",
            "exec(",
            "compile(",
            "__import__(",
            "subprocess.",
            "os.system(",
            "os.popen(",
            "open(",
            "file(",
            "input(",
            "raw_input(",
        ]

        for func in dangerous_functions:
            if func in code_content:
                patterns.append(func.rstrip("("))

        return patterns

    async def _initialize_virtual_environment(self) -> None:
        """5. 🐍 初始化Python虚拟环境"""
        self._plugin_logger.info(f"初始化Python虚拟环境: {self.plugin_name}")

        # 检查workspace_dir是否为None
        if self.workspace_dir is None:
            raise RuntimeError("工作目录未设置，无法创建虚拟环境")

        venv_path = self.workspace_dir / ".venv"
        self.virtual_env_path = venv_path

        # 检查虚拟环境是否已存在且有效
        if await self._check_virtual_env_valid(venv_path):
            self._plugin_logger.info(f"使用现有虚拟环境: {venv_path}")
            await self._setup_python_interpreter_path()
            return

        # self._plugin_logger.info(f"创建Python虚拟环境: {venv_path}")

        # 删除现有的无效虚拟环境
        if venv_path.exists():
            try:
                shutil.rmtree(venv_path)
                self._plugin_logger.info(f"删除现有虚拟环境: {venv_path}")
            except Exception as e:
                self._plugin_logger.exception("删除现有虚拟环境失败")
                raise RuntimeError(f"删除现有虚拟环境失败: {str(e)}")
            # 等待一下确保文件系统操作完成
            await asyncio.sleep(0.5)

        # 选择创建方式：UV或系统Python venv

        if not self.uv_path:
            raise RuntimeError("uv_path未设置")

        await self._create_venv_with_uv(venv_path)

        # 验证虚拟环境是否创建成功
        if not venv_path.exists():
            raise RuntimeError(f"虚拟环境目录未创建: {venv_path}")

        # 设置Python解释器路径
        await self._setup_python_interpreter_path()

        # 验证Python解释器
        await self._verify_python_interpreter()

        # 记录环境信息
        env_info = {
            "venv_path": str(venv_path),
            "python_interpreter": self.python_interpreter_path,
            "python_version": await self._get_python_version(),
            "created_at": datetime.now().isoformat(),
            "creation_method": "uv" if self.uv_path else "python_venv",
        }

        for key, value in env_info.items():
            self.environment_info[key] = value

        self._plugin_logger.info(f"Python虚拟环境初始化完成: {venv_path}")

    async def _create_venv_with_uv(self, venv_path: Path) -> None:
        """使用UV创建虚拟环境"""
        # self._plugin_logger.info(f"使用UV创建虚拟环境: {venv_path}")

        plugin_settings = get_settings().plugin

        # 使用UV创建虚拟环境 - 修正命令格式
        cmd = [
            self.uv_path,
            "venv",
            str(venv_path.absolute()),
            "--python",
            plugin_settings.python_version,
        ]

        # 添加系统包访问权限
        if plugin_settings.allow_system_packages:
            cmd.append("--system-site-packages")

        # 添加详细输出
        if plugin_settings.uv_verbose:
            cmd.append("--verbose")

        # 设置缓存目录
        if plugin_settings.uv_cache_dir:
            cmd.extend(["--cache-dir", plugin_settings.uv_cache_dir])

        # 设置环境变量，确保与命令行环境一致
        env = self._prepare_installation_environment()

        self._plugin_logger.info(f"执行UV命令: {' '.join(cmd)}")
        self._plugin_logger.trace(f"env: {env}")

        start_time = datetime.now()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_dir),
                env=env,
            )

            # 增加超时时间以应对网络问题
            timeout = int(plugin_settings.uv_venv_timeout)
            self._plugin_logger.info(f"UV虚拟环境创建中，超时时间: {timeout}秒")

            # 等待进程完成
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except TimeoutError:
                self._plugin_logger.error(
                    f"UV创建虚拟环境超时（{timeout}秒），正在终止进程"
                )
                try:
                    process.kill()
                    await asyncio.wait_for(process.wait(), timeout=10)
                except Exception:
                    self._plugin_logger.exception("终止UV进程失败")
                raise RuntimeError(f"UV创建虚拟环境超时（{timeout}秒）")

            # 记录输出信息用于调试
            stdout_text = stdout.decode() if stdout else ""
            stderr_text = stderr.decode() if stderr else ""

            if stdout_text:
                self._plugin_logger.info(f"UV stdout: {stdout_text}")
            if stderr_text:
                self._plugin_logger.info(f"UV stderr: {stderr_text}")

            if process.returncode != 0:
                self._plugin_logger.error(
                    f"UV命令执行失败，返回码: {process.returncode}"
                )
                self._plugin_logger.error(f"错误输出: {stderr_text}")
                raise RuntimeError(
                    f"UV创建虚拟环境失败 (返回码: {process.returncode}): {stderr_text}"
                )

            self._plugin_logger.info(
                f"UV虚拟环境创建命令执行成功, 耗时: {datetime.now() - start_time}"
            )

        except TimeoutError:
            self._plugin_logger.error(f"UV创建虚拟环境超时（{timeout}秒）")
            raise RuntimeError(f"UV创建虚拟环境超时（{timeout}秒）")
        except Exception as e:
            self._plugin_logger.error(f"UV创建虚拟环境异常: {str(e)}")
            raise RuntimeError(f"UV创建虚拟环境异常: {str(e)}")

    async def _setup_python_interpreter_path(self) -> None:
        """设置Python解释器路径"""
        if not self.virtual_env_path:
            raise RuntimeError("虚拟环境路径未设置")

        python_paths = [
            self.virtual_env_path / "bin" / "python",
            self.virtual_env_path / "bin" / "python3",
            self.virtual_env_path / "Scripts" / "python.exe",  # Windows
        ]

        for path in python_paths:
            if path.exists():
                self.python_interpreter_path = str(path.absolute())
                self._plugin_logger.info(
                    f"设置Python解释器路径: {self.python_interpreter_path}"
                )
                return

        # 如果找不到Python解释器，列出目录内容进行调试
        self._plugin_logger.error(
            f"虚拟环境目录内容: {list(self.virtual_env_path.iterdir()) if self.virtual_env_path.exists() else 'virtual_env_path目录不存在'}",
        )

        # 检查可能的子目录
        for subdir in ["bin", "Scripts"]:
            subdir_path = self.virtual_env_path / subdir
            if subdir_path.exists():
                self._plugin_logger.error(
                    f"{subdir} 目录内容: {list(subdir_path.iterdir())}"
                )

        raise RuntimeError(
            f"虚拟环境中未找到Python解释器: {[str(p) for p in python_paths]}"
        )

    async def _verify_python_interpreter(self) -> None:
        """验证Python解释器是否能正常工作"""
        if (
            not self.python_interpreter_path
            or not Path(self.python_interpreter_path).exists()
        ):
            raise RuntimeError(f"Python解释器不存在: {self.python_interpreter_path}")

        try:
            process = await asyncio.create_subprocess_exec(
                self.python_interpreter_path,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                version = stdout.decode().strip()
                self._plugin_logger.info(f"Python解释器验证成功: {version}")
            else:
                raise RuntimeError(f"Python解释器验证失败: {stderr.decode()}")
        except Exception as e:
            raise RuntimeError(f"Python解释器验证异常: {e}")

    async def _install_dependencies(self) -> None:
        """6.  安装所有依赖包"""
        self._plugin_logger.info(f"安装插件依赖: {self.plugin_name}")

        # 检查workspace_dir是否为None
        if not self.workspace_dir:
            raise RuntimeError("工作目录未设置，无法安装依赖")

        requirements_file = self.workspace_dir / "requirements.txt"
        if not requirements_file.exists():
            self._plugin_logger.error("未找到requirements.txt文件")
            self.environment_info["dependencies"] = {
                "status": "no_requirements",
                "packages": [],
            }
            raise RuntimeError("未找到requirements.txt文件")

        # 读取requirements.txt分析依赖
        requirements = []
        try:
            with open(requirements_file, encoding="utf-8") as f:
                requirements = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
            self._plugin_logger.info(f"发现 {len(requirements)} 个依赖包")
        except Exception as e:
            raise RuntimeError(f"读取requirements.txt失败: {e}")

        env = self._prepare_installation_environment()

        start_time = datetime.now()

        success = await self._install_dependency(
            str(requirements_file.absolute()), env, max_retries=3
        )

        # 记录安装结果
        self.environment_info["dependencies"] = {
            "status": success,
            "total": len(requirements),
            "installed": len(requirements),
            "install_time": datetime.now().isoformat(),
        }

        self._plugin_logger.info(
            f"依赖安装完成，耗时: {datetime.now() - start_time} - 依赖清单: {requirements}"
        )

    def _prepare_installation_environment(self) -> dict[str, str]:
        """准备安装环境变量"""

        # 设置环境变量，确保与命令行环境一致
        env = os.environ.copy()

        plugin_settings = get_settings().plugin

        # 添加代理设置
        if plugin_settings.http_proxy:
            env["HTTP_PROXY"] = plugin_settings.http_proxy
            env["http_proxy"] = plugin_settings.http_proxy
        if plugin_settings.https_proxy:
            env["HTTPS_PROXY"] = plugin_settings.https_proxy
            env["https_proxy"] = plugin_settings.https_proxy
        if plugin_settings.no_proxy:
            env["NO_PROXY"] = plugin_settings.no_proxy
            env["no_proxy"] = plugin_settings.no_proxy

        # 设置Python相关环境变量
        env["PYTHONUNBUFFERED"] = "1"  # 确保输出不被缓冲
        env["PYTHONIOENCODING"] = "utf-8"  # 设置编码

        # 设置UV相关环境变量以解决网络超时问题
        env["UV_HTTP_TIMEOUT"] = str(plugin_settings.uv_http_timeout)  # 设置HTTP超时
        env["UV_CONCURRENT_DOWNLOADS"] = str(
            plugin_settings.uv_concurrent_downloads
        )  # 减少并发下载数量
        env["UV_RETRY_ATTEMPTS"] = str(plugin_settings.uv_retry_attempts)  # 设置重试次数

        # 设置UV的索引URL环境变量
        env["UV_INDEX_URL"] = str(plugin_settings.pip_index_url)
        env["UV_PYTHON_INSTALL_MIRROR"] = str(plugin_settings.uv_python_install_mirror)

        # 设置虚拟环境
        env["VIRTUAL_ENV"] = str(self.virtual_env_path)

        # 确保PATH包含UV路径
        if self.uv_path:
            uv_dir = str(Path(self.uv_path).parent)
            if uv_dir not in env.get("PATH", ""):
                env["PATH"] = f"{uv_dir}:{env.get('PATH', '')}"

        return env

    async def _install_dependency(
        self, requirement: str, env: dict[str, str], max_retries: int = 3
    ) -> bool:
        """安装单个依赖包，支持重试"""

        plugin_settings = get_settings().plugin

        if not self.virtual_env_path:
            raise RuntimeError("virtual_env_path未设置")

        for attempt in range(max_retries):
            try:
                # 根据操作系统选择不同的激活方式
                is_windows = platform.system() == "Windows"

                # 构建UV pip install命令参数
                uv_cmd_parts = [
                    f"{self.uv_path}" if self.uv_path else "uv",
                    "pip",
                    "install",
                    "-r",
                    f"{requirement}",
                ]

                # 添加额外的pip参数
                if plugin_settings.pip_index_url:
                    uv_cmd_parts.extend(["--index-url", plugin_settings.pip_index_url])
                if plugin_settings.pip_trusted_host:
                    uv_cmd_parts.extend(
                        ["--trusted-host", plugin_settings.pip_trusted_host]
                    )
                if plugin_settings.allow_system_packages:
                    uv_cmd_parts.append("--system-site-packages")
                if plugin_settings.uv_verbose:
                    uv_cmd_parts.append("--verbose")
                if plugin_settings.uv_cache_dir:
                    uv_cmd_parts.extend(["--cache-dir", plugin_settings.uv_cache_dir])

                # 构建完整的UV命令
                uv_full_cmd = " ".join(uv_cmd_parts)

                if is_windows:
                    # Windows系统：使用call命令调用activate.bat
                    # activate_script = self.virtual_env_path / "Scripts" / "activate.bat"
                    # shell_command = f'call "{activate_script}" && {uv_full_cmd}'
                    cmd = ["cmd", "/c", uv_full_cmd]
                else:
                    # Unix/Linux/macOS系统：使用source命令
                    activate_script = self.virtual_env_path / "bin" / "activate"
                    shell_command = f'source "{activate_script}" && {uv_full_cmd}'
                    cmd = ["bash", "-c", shell_command]

                self._plugin_logger.debug(
                    f"安装依赖 (尝试 {attempt + 1}/{max_retries}): {requirement}"
                )
                timeout = plugin_settings.plugin_dependency_timeout

                self._plugin_logger.info(f"执行安装命令: {' '.join(cmd)}")
                self._plugin_logger.trace(f"env: {env}")

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.workspace_dir,
                    env=env,
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=int(timeout)
                )

                if process.returncode == 0:
                    self._plugin_logger.info(f"依赖安装成功: {requirement}")
                    return True
                else:
                    error_msg = stderr.decode() if stderr else "未知错误"
                    self._plugin_logger.warning(
                        f"依赖安装失败 (尝试 {attempt + 1}): {requirement}, 错误: {error_msg}"
                    )

                    # 如果是最后一次尝试，记录详细错误
                    if attempt == max_retries - 1:
                        self._plugin_logger.error(f"依赖安装最终失败: {requirement}")

            except TimeoutError:
                self._plugin_logger.warning(
                    f"依赖安装超时 (尝试 {attempt + 1}): {requirement}"
                )
                if process:
                    process.terminate()
                    await process.wait()
            except Exception as e:
                self._plugin_logger.warning(
                    f"依赖安装异常 (尝试 {attempt + 1}): {requirement}, 错误: {e}"
                )

            # 在重试之前等待一小段时间
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)  # 指数退避

        return False

    async def _precompile_python_files(self) -> None:
        """7.  预编译Python文件"""

        if not get_settings().plugin.enable_precompile:
            self._plugin_logger.info("预编译已禁用，跳过")
            self.environment_info["precompile"] = {"status": "disabled"}
            return

        self._plugin_logger.info(f"预编译Python文件: {self.plugin_name}")

        cmd = [
            self.python_interpreter_path,
            "-m",
            "compileall",
            "-b",
            str(self.workspace_dir),
        ]

        self._plugin_logger.info(f"预编译Python文件命令: {' '.join(cmd)}")

        start_time = datetime.now()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_dir,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)

            if process.returncode == 0:
                self._plugin_logger.info(
                    f"Python文件预编译成功: {self.plugin_name} - 耗时: {datetime.now() - start_time}",
                )
                self.environment_info["precompile"] = {
                    "status": "success",
                    "compiled_at": datetime.now().isoformat(),
                }
            else:
                self._plugin_logger.warning(
                    f"Python文件预编译失败: {stderr.decode() if stderr else '未知错误'}"
                )
                self.environment_info["precompile"] = {
                    "status": "failed",
                    "error": stderr.decode() if stderr else "未知错误",
                }

        except TimeoutError:
            self._plugin_logger.warning(f"Python文件预编译超时: {self.plugin_name}")
            self.environment_info["precompile"] = {"status": "timeout"}
        except Exception as e:
            self._plugin_logger.warning(f"Python文件预编译出错: {e}")
            self.environment_info["precompile"] = {"status": "error", "error": str(e)}

    async def _generate_runtime_manifest(self) -> None:
        """9.  生成运行时清单"""
        self._plugin_logger.info(f"生成运行时清单: {self.plugin_name}")

        if not self.workspace_dir:
            raise RuntimeError("workspace_dir未设置")

        manifest = {
            "plugin_info": {
                "name": self.plugin_name,
                "version": self.plugin_version,
                "author": self.plugin_config.configuration.author,
            },
            "preparation_info": {
                "prepared_at": self.prepared_at.isoformat()
                if self.prepared_at
                else datetime.now().isoformat(),
                "workspace_dir": str(self.workspace_dir),
                "virtual_env_path": str(self.virtual_env_path)
                if self.virtual_env_path
                else None,
                "python_interpreter": self.python_interpreter_path,
            },
            "environment_info": self.environment_info,
            "runtime_config": {
                "entrypoint": self._get_entrypoint(),
                "language": self._get_language(),
                "memory_limit": self._get_memory_limit(),
            },
        }

        # 保存运行时清单
        manifest_file = self.workspace_dir / "config" / "runtime_manifest.json"
        manifest_file.parent.mkdir(parents=True, exist_ok=True)

        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        self._plugin_logger.info(f"运行时清单已保存: {manifest_file}")

    async def _preconfigure_resources(self) -> None:
        """10.  预分配资源配置"""
        self._plugin_logger.info(f"预配置资源: {self.plugin_name}")

        # 计算内存需求
        memory_requirement = 268435456  # 默认256MB
        if (
            self.plugin_config.configuration.resource
            and self.plugin_config.configuration.resource.memory
        ):
            memory_requirement = self.plugin_config.configuration.resource.memory

        # 预分配权限配置
        permissions = {
            "network_access": self.permissions.can_access_network(),
            "file_system_paths": self.permissions.file_system_access,
            "environment_variables": self.permissions.env_vars_access,
            "subprocess_access": self.permissions.can_use_subprocess(),
        }

        # 保存资源配置
        resource_config = {
            "memory_limit": memory_requirement,
            "permissions": permissions,
            "security_profile": {
                "strict_mode": get_settings().plugin.strict_security_mode,
            },
            "configured_at": datetime.now().isoformat(),
        }

        config_file = self.workspace_dir / "config" / "resource_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(resource_config, f, indent=2, ensure_ascii=False)

        self.environment_info["resource_config"] = resource_config
        self._plugin_logger.info(f"资源配置完成: {self.plugin_name}")

    # ==================== 启动方法（轻量级操作）====================

    async def _start_plugin_process(self) -> None:
        """启动插件进程"""
        self._plugin_logger.info(f"启动插件进程: {self.plugin_name}")

        # 读取运行时清单
        manifest_file = self.workspace_dir / "config" / "runtime_manifest.json"
        if manifest_file.exists():
            with open(manifest_file, encoding="utf-8") as f:
                manifest = json.load(f)
                entrypoint = manifest["runtime_config"]["entrypoint"]
        else:
            entrypoint = "main"  # 默认入口点

        entrypoint_file = self.workspace_dir / f"{entrypoint}.py"

        if not self.virtual_env_path or not self.python_interpreter_path:
            raise RuntimeError("virtual_env_path或者python_interpreter_path不存在")

        # 使用虚拟环境中的Python解释器
        venv_python = self.python_interpreter_path
        is_windows = platform.system() == "Windows"

        # 构建Python执行命令
        if entrypoint_file.exists():
            python_cmd = f"{venv_python} {entrypoint_file}"
        else:
            python_cmd = f"{venv_python} -m {entrypoint}"

        if is_windows:
            # Windows系统：使用call命令调用activate.bat
            # activate_script = self.virtual_env_path / "Scripts" / "activate.bat"
            # shell_command = f'call "{activate_script}" && {python_cmd}'
            cmd = ["cmd", "/c", python_cmd]
        else:
            # Unix/Linux/macOS系统：使用source命令
            activate_script = self.virtual_env_path / "bin" / "activate"
            shell_command = f'source "{activate_script}" && {python_cmd}'
            cmd = ["bash", "-c", shell_command]

        self._plugin_logger.info(f"使用Python解释器: {venv_python}")
        self._plugin_logger.info(f"启动命令: {' '.join(cmd)}")

        # 设置环境变量
        env = self._prepare_runtime_environment()

        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_dir,
                env=env,
            )

            self.process_id = self.process.pid
            self._plugin_logger.info(f"插件进程启动成功: PID {self.process_id}")

            # 启动输出处理任务和响应读取器
            self._output_task = asyncio.create_task(self._handle_process_output())
            await self._start_response_reader()

        except Exception as e:
            raise RuntimeError(f"启动插件进程失败: {e}")

    def _prepare_runtime_environment(self) -> dict[str, str]:
        """准备运行时环境变量"""
        env = os.environ.copy()

        author = self.plugin_config.configuration.author
        author = author if author else "unknown"
        name: str = self.plugin_config.configuration.name
        version = self.plugin_config.configuration.version

        plugin_id = author + "/" + name

        env.update(
            {
                "PYTHONUNBUFFERED": "1",
                "VIRTUAL_ENV": str(self.virtual_env_path),
                # 基本插件信息
                "PLUGIN_ID": plugin_id,
                "PLUGIN_VERSION": version,
                "PLUGIN_NAME": name,
                "PLUGIN_AUTHOR": author,
                "PLUGIN_WORKSPACE": str(self.workspace_dir),
                # Dify Plugin特定环境变量
                "DIFY_PLUGIN_ID": plugin_id,
                "DIFY_PLUGIN_VERSION": version,
                "DIFY_PLUGIN_TYPE": "plugin",
                "DIFY_PLUGIN_NAME": name,
                "DIFY_PLUGIN_AUTHOR": author,
                "DIFY_PLUGIN_WORKSPACE": str(self.workspace_dir),
                "DIFY_PLUGIN_LOG_LEVEL": "DEBUG",
                # 通信相关环境变量
                "PLUGIN_SERVER_HOST": "127.0.0.1",
                "PLUGIN_SERVER_PORT": str(self.port) if self.port else "0",
                "PLUGIN_ENDPOINT": f"http://127.0.0.1:{self.port}/{name}"
                if self.port
                else "",
            },
        )
        return env

    async def _wait_for_plugin_ready(self) -> None:
        """等待插件就绪"""
        self._plugin_logger.info(f"等待插件就绪: {self.plugin_name}")

        max_wait = 20  # 最多等待20秒
        start_time = time.time()

        # 先等待短时间让插件初始化
        await asyncio.sleep(1.0)

        while time.time() - start_time < max_wait:
            if self.process and self.process.returncode is not None:
                # 进程意外退出
                await self._handle_process_exit_during_startup()
                raise RuntimeError("插件进程意外退出")

            # 检查就绪状态
            if await self._check_plugin_readiness():
                self._plugin_ready = True
                self._plugin_logger.info(f"插件就绪确认: {self.plugin_name}")
                return

            await asyncio.sleep(0.5)

        # 超时检查 - 如果进程仍在运行，认为就绪
        if self.process and self.process.returncode is None:
            self._plugin_ready = True
            self._plugin_logger.info(f"插件进程运行中，认为已就绪: {self.plugin_name}")
            return

        raise RuntimeError(f"插件启动超时: {self.plugin_name}")

    async def _check_plugin_readiness(self) -> bool:
        """检查插件是否就绪"""
        # 基于内存标志判断就绪状态，需要同时收到插件元数据和心跳
        return self._plugin_metadata_received and self._plugin_heartbeat_received

    async def _handle_process_exit_during_startup(self) -> None:
        """处理启动过程中的进程退出"""
        try:
            if self.log_file and self.log_file.exists():
                with open(self.log_file, encoding="utf-8") as f:
                    log_content = f.read()
                self._plugin_logger.error(f"插件启动失败，日志内容: {log_content}")
        except Exception:
            pass

        self._plugin_logger.error(
            f"插件进程退出，返回码: {self.process.returncode if self.process else 'None'}"
        )

    async def _register_monitoring(self) -> None:
        """注册监控"""
        self._plugin_logger.debug(f"注册插件监控: {self.plugin_name}")
        # 这里可以注册到监控系统
        # 暂时只是记录状态
        pass

    async def _setup_runtime_security(self) -> None:
        """设置进程安全限制"""
        self._plugin_logger.debug(f"设置运行时安全限制: {self.plugin_name}")

        # 读取资源配置
        config_file = self.workspace_dir / "config" / "resource_config.json"
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                resource_config = json.load(f)

            # 根据配置设置安全限制
            # 这里可以实现进程资源限制
            pass

    async def _cleanup_on_start_failure(self) -> None:
        """启动失败时的清理"""
        self._plugin_logger.info(f"清理启动失败的资源: {self.plugin_name}")

        if self.process:
            try:
                if self.process.returncode is None:
                    self.process.terminate()
                    await asyncio.sleep(2)
                    if self.process.returncode is None:
                        self.process.kill()
            except Exception as e:
                self._plugin_logger.error(f"清理进程时出错: {e}")
            finally:
                self.process = None
                self.process_id = None
                self.port = None

        if self._output_task and not self._output_task.done():
            self._output_task.cancel()

    # ==================== 工具方法 ====================

    def _get_entrypoint(self) -> str:
        """获取插件入口点"""
        if (
            self.plugin_config.configuration.meta
            and self.plugin_config.configuration.meta.runner
            and self.plugin_config.configuration.meta.runner.entrypoint
        ):
            return self.plugin_config.configuration.meta.runner.entrypoint
        return "main"

    def _get_language(self) -> str:
        """获取插件语言"""
        if (
            self.plugin_config.configuration.meta
            and self.plugin_config.configuration.meta.runner
            and self.plugin_config.configuration.meta.runner.language
        ):
            return self.plugin_config.configuration.meta.runner.language.value
        return "python"

    def _get_memory_limit(self) -> int | None:
        """获取内存限制"""
        if (
            self.plugin_config.configuration.resource
            and self.plugin_config.configuration.resource.memory
        ):
            return self.plugin_config.configuration.resource.memory
        return None

    async def _check_virtual_env_valid(self, venv_path: Path) -> bool:
        """检查虚拟环境是否有效"""
        if not venv_path.exists():
            return False

        # 检查多个可能的Python路径
        python_paths = [
            venv_path / "bin" / "python",
            venv_path / "bin" / "python3",
            venv_path / "Scripts" / "python.exe",  # Windows
        ]

        python_path = None
        for path in python_paths:
            if path.exists():
                python_path = path
                break

        if not python_path:
            return False

        # 检查Python是否可以正常运行
        try:
            process = await asyncio.create_subprocess_exec(
                str(python_path),
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception:
            return False

    async def _get_python_version(self) -> str:
        """获取Python版本"""

        if not self.python_interpreter_path:
            return "unknown"

        try:
            process = await asyncio.create_subprocess_exec(
                self.python_interpreter_path,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            return stdout.decode().strip() if process.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    async def _handle_process_output(self):
        """处理插件进程的输出 - 现在主要处理stderr"""
        if not self.process:
            return

        try:
            # 创建日志文件写入器
            with open(self.log_file, "w", encoding="utf-8") as log_file:
                # 只处理stderr，stdout由新的响应读取器处理

                async def read_stderr():
                    while self.process and self.process.returncode is None:
                        try:
                            if self.process.stderr:
                                line = await self.process.stderr.readline()
                                if line:
                                    content = line.decode("utf-8", errors="ignore")
                                    log_file.write(
                                        f"{time.strftime('%Y-%m-%d %H:%M:%S')} - STDERR: {content}"
                                    )
                                    log_file.flush()
                                    self._plugin_logger.warning(
                                        f"插件错误输出: {content.strip()}"
                                    )
                                else:
                                    # 没有更多输出，短暂等待
                                    await asyncio.sleep(0.1)
                        except Exception as e:
                            self._plugin_logger.error(f"读取stderr时出错: {e}")
                            break

                await read_stderr()

        except Exception as e:
            self._plugin_logger.error(f"处理插件输出时出错: {e}")

    async def _start_response_reader(self):
        """启动专门的响应读取器，处理并发响应"""
        if not self.process:
            return

        self._plugin_logger.debug("启动响应读取器")

        async def response_reader():
            """持续读取stdout并分发响应"""
            response_buffer = ""

            while self.process and self.process.returncode is None:
                try:
                    if not self.process.stdout:
                        continue

                    # 读取数据块
                    chunk = await asyncio.wait_for(
                        self.process.stdout.read(8192), timeout=1.0
                    )
                    if not chunk:
                        await asyncio.sleep(0.1)
                        continue

                    chunk_str = chunk.decode("utf-8", errors="ignore")
                    response_buffer += chunk_str

                    # 记录stdout到日志文件
                    self._log_stdout(chunk_str)

                    # 处理缓冲区中的完整消息（以换行符分隔）
                    while "\n" in response_buffer:
                        line, response_buffer = response_buffer.split("\n", 1)
                        line_str = line.strip()

                        if not line_str:
                            continue

                        # 解析响应并分发
                        await self._dispatch_response(line_str)

                except TimeoutError:
                    # 检查进程是否还活着
                    if self.process and self.process.returncode is not None:
                        self._plugin_logger.debug("插件进程已退出，停止响应读取器")
                        break
                    continue
                except Exception as e:
                    self._plugin_logger.error(f"响应读取器错误: {e}")
                    break

            self._plugin_logger.debug("响应读取器已停止")

        # 启动响应读取器任务
        self._response_reader_task = asyncio.create_task(response_reader())

    async def _dispatch_response(self, response_line: str):
        """分发响应到对应的等待者"""

        queue = None

        try:
            responseMessage = PluginMessageProtocol.parse_message(response_line)
            if not responseMessage:
                self._plugin_logger.info(f"非JSON响应: {response_line[:1000]}")
                return

            if isinstance(responseMessage, dict):
                self._plugin_logger.debug(f"收到普通响应: {responseMessage}")
                # 检查是否为插件元数据响应

                if (
                    responseMessage.get("type") == "plugin"
                    and responseMessage.get("version") is not None
                ):
                    # {'version': '0.0.5', 'type': 'plugin', 'author': 'langgenius', 'name': 'github', 'description': {'zh_Hans':
                    self._plugin_metadata_received = True
                    self._plugin_logger.debug("插件元数据已接收")
                else:
                    # 普通字典响应可能是需要分发的数据
                    session_id = responseMessage.get("session_id")
                    if session_id and session_id in self._streaming_requests:
                        self._plugin_logger.debug(f"分发普通字典响应到 session: {session_id}")
                        queue = self._streaming_requests[session_id]
                        await queue.put(responseMessage)
                return

            event = responseMessage.event
            self._plugin_logger.debug(f"收到事件响应: event={event}, session_id={responseMessage.session_id}")

            if event == Event.SESSION:
                # self._plugin_logger.debug(f"收到插件会话: {str(response_line)[:500]}...")
                # 获取session_id
                session_id = responseMessage.session_id
                if not session_id:
                    self._plugin_logger.warning("响应缺少session_id")
                    return

                # 查找对应的等待者
                if session_id not in self._streaming_requests:
                    self._plugin_logger.warning(
                        f"未找到等待者，session_id: {session_id}"
                    )
                    return

                queue = self._streaming_requests[session_id]

                # 查找对应的等待者
                result = responseMessage.data
                if not isinstance(result, dict):
                    self._plugin_logger.warning(f"收到插件响应，非字典类型: {result}")
                    return

                # 记录响应内容
                self._plugin_logger.debug(f"收到 SESSION 响应: type={result.get('type')}, keys={list(result.keys())}")

                is_end_message = result.get("type", None) == "end"
                is_error_message = result.get("type", None) == "error"
                if is_error_message:
                    self._plugin_logger.error(f"收到插件错误: {result}")

                    error_data = result.get("data", result)
                    raise PluginCommunicationError(
                        f"收到插件错误: {error_data}", error_data
                    )

                # 处理流式请求
                if session_id in self._streaming_requests:
                    try:
                        if is_end_message:
                            # 结束消息：发送None表示流结束，然后清理
                            await queue.put(None)
                            # self._plugin_logger.debug(f"流式响应结束，session: {session_id}")
                        else:
                            # 流式数据：放入队列
                            await queue.put(result)
                    except Exception as e:
                        self._plugin_logger.exception("处理流式响应失败")
                        raise e

                else:
                    self._plugin_logger.warning(
                        f"未找到等待者，session_id: {session_id}"
                    )

            elif event == Event.HEARTBEAT:
                # {"event":"heartbeat","session_id":null,"data":{}}...
                self._plugin_heartbeat_received = True

                # 控制心跳日志打印频率，超过5分钟才打印一次
                current_time = datetime.now()
                if (
                    self._last_heartbeat_log_time is None
                    or (current_time - self._last_heartbeat_log_time).total_seconds()
                    > 300  # 5分钟
                ):
                    self._plugin_logger.debug(
                        f"收到插件心跳: {str(response_line)[:1000]}"
                    )
                    self._last_heartbeat_log_time = current_time
            elif event == Event.LOG:
                self._plugin_logger.debug(f"收到插件日志: {str(response_line)[:1000]}")
            elif event == Event.ERROR:
                self._plugin_logger.error(f"收到插件错误2: {str(response_line)[:1000]}")
            else:
                self._plugin_logger.debug(f"无效消息格式: {str(response_line)[:1000]}")
                return

        except Exception as e:
            self._plugin_logger.error(f"分发响应时出错: {e}")
            if queue:
                await queue.put(Exception(e))

    async def _send_message_stream(
        self,
        invoke_request: dict[str, Any],
        timeout: int,
        session_id: str | None = None,
    ):
        """向插件发送消息并等待流式响应 - 支持并发调用"""

        if not self.process or self.process.returncode is not None:
            raise PluginError("插件进程未运行，请重启插件")

        try:
            message = PluginMessageProtocol.create_request_message(
                invoke_request, session_id
            )
            actual_session_id = message.session_id

            # 创建队列用于流式响应
            response_queue = asyncio.Queue()

            # 注册到流式请求
            self._streaming_requests[actual_session_id] = response_queue

            # 注册开始时间
            self._streaming_start_time[actual_session_id] = time.time()

            try:
                # self._plugin_logger.debug(f"发送消息到插件: {message}")

                if not self.process.stdin:
                    return

                # 发送消息
                self.process.stdin.write(PluginMessageProtocol.to_bytes(message))
                await self.process.stdin.drain()
                self._plugin_logger.debug("消息已发送到插件stdin")

                # 记录最后消息时间，用于超时检查
                last_message_time = time.time()

                # 创建超时检查任务（只创建一次）
                async def timeout_checker():
                    nonlocal last_message_time
                    while True:
                        await asyncio.sleep(1.0)  # 每秒检查一次
                        current_time = time.time()
                        if current_time - last_message_time > timeout:
                            raise PluginTimeoutError(
                                f"等待插件流式响应超时 ({timeout}s)"
                            )

                timeout_task = asyncio.create_task(timeout_checker())

                try:
                    while True:
                        # 等待响应或超时
                        get_task = asyncio.create_task(response_queue.get())
                        done, pending = await asyncio.wait(
                            [get_task, timeout_task],
                            return_when=asyncio.FIRST_COMPLETED,
                        )

                        if timeout_task in done:
                            # 超时了
                            get_task.cancel()
                            if actual_session_id in self._streaming_requests:
                                del self._streaming_requests[actual_session_id]
                            raise PluginTimeoutError(
                                f"等待插件流式响应超时 ({timeout}s)"
                            )

                        # 获取响应数据
                        result = get_task.result()

                        if result is None:
                            # 流结束
                            cost_time = -1
                            if actual_session_id in self._streaming_start_time:
                                cost_time = (
                                    time.time()
                                    - self._streaming_start_time[actual_session_id]
                                )
                                del self._streaming_start_time[actual_session_id]

                            self._plugin_logger.debug(
                                f"流式响应完成，session: {actual_session_id}, 耗时: {cost_time:.2f}秒",
                            )

                            # 清理资源
                            if actual_session_id in self._streaming_requests:
                                del self._streaming_requests[actual_session_id]

                            break
                        elif isinstance(result, Exception):
                            # 错误
                            raise result
                        else:
                            # 流式数据 - 更新最后消息时间（无需重新创建Task）
                            last_message_time = time.time()
                            # self._plugin_logger.debug(f"yield流式数据，session: {actual_session_id}")

                            yield result

                except asyncio.CancelledError as e:
                    # 清理资源
                    if actual_session_id in self._streaming_requests:
                        del self._streaming_requests[actual_session_id]
                    raise e
                finally:
                    # 确保超时任务被取消
                    if not timeout_task.done():
                        timeout_task.cancel()

            except Exception as e:
                # 清理失败的请求
                if actual_session_id in self._streaming_requests:
                    del self._streaming_requests[actual_session_id]
                raise e

        except Exception as e:
            if isinstance(e, PluginCommunicationError | PluginTimeoutError):
                raise e
            self._plugin_logger.error(f"发送流式消息失败: {e}")
            raise PluginCommunicationError(f"流式通讯失败: {e}")

    def _log_stdout(self, line_str: str):
        """记录stdout到日志文件"""
        try:
            with open(self.log_file, "a", encoding="utf-8") as log_file:
                log_file.write(
                    f"{time.strftime('%Y-%m-%d %H:%M:%S')} - STDOUT: {line_str}"
                )
                log_file.flush()
        except Exception:
            pass  # 忽略日志写入错误
