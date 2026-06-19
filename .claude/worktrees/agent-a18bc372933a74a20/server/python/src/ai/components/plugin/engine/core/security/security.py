"""
插件安全管理器
提供插件安全验证、隔离和监控功能
包含文件访问控制、网络访问限制、代码扫描等安全机制
"""

import os
import re
import sys
from pathlib import Path
from typing import Any

import psutil

# from cryptography.hazmat.primitives import hashes, serialization
# from cryptography.hazmat.primitives.asymmetric import  padding
from loguru import logger

from ai.components.plugin.engine.config.settings import plugin_settings


class SecurityViolationError(Exception):
    """安全违规异常"""

    pass


class FileAccessMonitor:
    """文件访问监控器"""

    def __init__(self, allowed_paths: list[str]):
        self.allowed_paths = [os.path.normpath(p) for p in allowed_paths]

    def check_file_access(self, file_path: str, mode: str = "r") -> bool:
        """检查文件访问权限"""
        normalized_path = os.path.normpath(file_path)

        # 检查是否在允许的路径范围内
        for allowed_path in self.allowed_paths:
            if normalized_path.startswith(allowed_path):
                return True

        # 特殊情况：Python标准库路径
        if any(normalized_path.startswith(p) for p in sys.path):
            return True

        return False

    def safe_open(self, file_path: str, mode: str = "r", **kwargs):
        """安全的文件打开函数"""
        if not self.check_file_access(file_path, mode):
            raise SecurityViolationError(f"文件访问被拒绝: {file_path}")

        return open(file_path, mode, **kwargs)


class NetworkAccessMonitor:
    """网络访问监控器"""

    def __init__(self, allowed_hosts: list[str], blocked_ports: list[int]):
        self.allowed_hosts = allowed_hosts
        self.blocked_ports = set(blocked_ports)

    def check_network_access(self, host: str, port: int) -> bool:
        """检查网络访问权限"""
        # 检查端口黑名单
        if port in self.blocked_ports:
            return False

        # 检查主机白名单
        if "*" in self.allowed_hosts:
            return True

        return any(
            host == allowed_host or host.endswith(f".{allowed_host}")
            for allowed_host in self.allowed_hosts
        )

    def safe_connect(self, host: str, port: int):
        """安全的网络连接检查"""
        if not self.check_network_access(host, port):
            raise SecurityViolationError(f"网络访问被拒绝: {host}:{port}")


class CodeScanner:
    """代码安全扫描器"""

    def __init__(self):
        # 危险函数模式（更严格的检查）
        self.dangerous_patterns = [
            # 系统调用
            (r"os\.system\s*\([^)]*\)", "系统命令执行"),
            (r"subprocess\.(call|run|Popen)\s*\([^)]*\)", "子进程调用"),
            (r"commands\.(getoutput|getstatusoutput)\s*\([^)]*\)", "命令执行"),
            # 代码执行
            (r"exec\s*\([^)]*\)", "动态代码执行"),
            (r"eval\s*\([^)]*\)", "表达式执行"),
            (r"compile\s*\([^)]*\)", "代码编译"),
            (r"__import__\s*\([^)]*\)", "动态导入"),
            # 文件操作
            (r'open\s*\([^)]*["\']w["\'][^)]*\)', "写文件操作"),
            (r'open\s*\([^)]*["\']a["\'][^)]*\)', "追加文件操作"),
            (r"os\.remove\s*\([^)]*\)", "删除文件"),
            (r"os\.rmdir\s*\([^)]*\)", "删除目录"),
            (r"shutil\.rmtree\s*\([^)]*\)", "递归删除"),
            # 权限操作
            (r"os\.chmod\s*\([^)]*777[^)]*\)", "危险权限设置"),
            (r"os\.chown\s*\([^)]*\)", "文件所有权更改"),
            # 网络操作
            (r"socket\.socket\s*\([^)]*\)", "原始套接字"),
            (r"urllib\.request\.urlopen\s*\([^)]*\)", "URL访问"),
            (r"requests\.(get|post|put|delete)\s*\([^)]*\)", "HTTP请求"),
            # 进程操作
            (r"os\.fork\s*\([^)]*\)", "进程分叉"),
            (r"multiprocessing\.Process\s*\([^)]*\)", "多进程"),
            (r"threading\.Thread\s*\([^)]*\)", "多线程"),
            # 反射和内省
            (r"getattr\s*\([^)]*\)", "属性获取"),
            (r"setattr\s*\([^)]*\)", "属性设置"),
            (r"hasattr\s*\([^)]*\)", "属性检查"),
            (r"vars\s*\([^)]*\)", "变量访问"),
            (r"globals\s*\([^)]*\)", "全局变量访问"),
            (r"locals\s*\([^)]*\)", "局部变量访问"),
        ]

        # 可疑导入
        self.suspicious_imports = [
            "subprocess",
            "multiprocessing",
            "socket",
            "urllib",
            "requests",
            "ftplib",
            "smtplib",
            "pickle",
            "marshal",
            "ctypes",
        ]

    def scan_code(self, code: str, file_path: str = "") -> list[dict[str, Any]]:
        """扫描代码并返回检测结果"""
        violations = []

        # 检查危险模式
        for pattern, description in self.dangerous_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = code[: match.start()].count("\n") + 1
                violations.append(
                    {
                        "type": "dangerous_function",
                        "description": description,
                        "pattern": pattern,
                        "line": line_num,
                        "code": match.group(0),
                        "file": file_path,
                        "severity": "high",
                    },
                )

        # 检查可疑导入
        import_pattern = r"(?:from\s+(\w+)|import\s+(\w+))"
        import_matches = re.finditer(import_pattern, code, re.IGNORECASE | re.MULTILINE)
        for match in import_matches:
            module_name = match.group(1) or match.group(2)
            if module_name in self.suspicious_imports:
                line_num = code[: match.start()].count("\n") + 1
                violations.append(
                    {
                        "type": "suspicious_import",
                        "description": f"可疑模块导入: {module_name}",
                        "module": module_name,
                        "line": line_num,
                        "code": match.group(0),
                        "file": file_path,
                        "severity": "medium",
                    },
                )

        return violations


class PermissionManager:
    """权限管理器"""

    def __init__(self, permissions_config: dict[str, Any]):
        self.network_access = permissions_config.get("network_access", False)
        self.file_system_access = permissions_config.get("file_system_access", [])
        self.subprocess_access = permissions_config.get("subprocess_access", False)
        self.allowed_hosts = permissions_config.get("internet_hosts", [])
        self.blocked_ports = permissions_config.get("blocked_ports", [])

        # 创建监控器
        self.file_monitor = FileAccessMonitor(self.file_system_access)
        self.network_monitor = NetworkAccessMonitor(
            self.allowed_hosts, self.blocked_ports
        )

    def check_file_permission(self, file_path: str, mode: str = "r") -> bool:
        """检查文件访问权限"""
        return self.file_monitor.check_file_access(file_path, mode)

    def check_network_permission(self, host: str, port: int) -> bool:
        """检查网络访问权限"""
        if not self.network_access:
            return False
        return self.network_monitor.check_network_access(host, port)

    def check_subprocess_permission(self) -> bool:
        """检查子进程权限"""
        return self.subprocess_access


class SecurityManager:
    """安全管理器"""

    def __init__(self):
        self.blocked_paths: set[str] = set(plugin_settings.blocked_directories)
        self.allowed_extensions: set[str] = set(plugin_settings.allowed_file_extensions)
        self.blocked_ports: set[int] = set(plugin_settings.blocked_ports)
        self.public_keys: list[Any] = []
        self.code_scanner = CodeScanner()

    def check_path_traversal(self, file_path: str) -> bool:
        """检查路径是否包含路径遍历攻击"""
        try:
            # 规范化路径，处理不同操作系统的路径分隔符
            normalized_path = os.path.normpath(file_path.replace("\\", "/"))

            # 检查是否包含 .. 组件（更严格的检查）
            path_parts = normalized_path.split("/")
            if ".." in path_parts:
                logger.warning(f"检测到路径遍历攻击: {file_path}")
                return False

            # 额外检查原始路径中的 .. 模式
            if ".." in file_path:
                logger.warning(f"检测到路径遍历攻击: {file_path}")
                return False

            # 检查是否访问被禁止的目录
            for blocked_dir in self.blocked_paths:
                if normalized_path.startswith(blocked_dir):
                    logger.warning(f"尝试访问被禁止的目录: {file_path}")
                    return False

            return True

        except Exception as e:
            logger.error(f"路径安全检查失败: {e}")
            return False

    def check_file_extension(self, file_path: str) -> bool:
        """检查文件扩展名是否被允许"""
        if not self.allowed_extensions:
            return True

        file_extension = Path(file_path).suffix.lower()
        allowed = file_extension in self.allowed_extensions

        if not allowed:
            logger.warning(f"不允许的文件扩展名: {file_path}")

        return allowed

    def setup_process_limits(self, pid: int) -> None:
        """设置进程资源限制"""
        if not plugin_settings.enable_process_isolation:
            return

        try:
            process = psutil.Process(pid)

            # 设置内存限制
            memory_limit = self._parse_memory_limit(plugin_settings.plugin_memory_limit)
            if memory_limit:
                # 注意：psutil在某些系统上可能不支持设置内存限制
                # 这里我们使用cgroups或者其他系统级别的方法
                self._set_memory_limit(pid, memory_limit)

            # 设置CPU限制（仅在支持的系统上）
            cpu_limit = self._parse_cpu_limit(plugin_settings.plugin_cpu_limit)
            if cpu_limit:
                try:
                    if hasattr(process, "cpu_affinity"):
                        # 限制到第一个CPU核心,
                        process.cpu_affinity([0])
                        logger.debug(f"已为进程 {pid} 设置CPU亲和性")
                    else:
                        logger.debug("系统不支持CPU亲和性设置")
                except (AttributeError, OSError, NotImplementedError) as e:
                    logger.debug(f"CPU亲和性设置不支持: {e}")

            logger.debug(f"进程 {pid} 资源限制设置完成")

        except Exception as e:
            # 改为debug级别，因为这些限制不是必需的
            logger.debug(f"设置进程限制失败（非关键错误）: {e}")

    def _parse_memory_limit(self, limit_str: str) -> int:
        """解析内存限制字符串"""
        if not limit_str:
            return 0

        limit_str = limit_str.upper()
        if limit_str.endswith("MB"):
            return int(limit_str[:-2]) * 1024 * 1024
        elif limit_str.endswith("GB"):
            return int(limit_str[:-2]) * 1024 * 1024 * 1024
        elif limit_str.endswith("KB"):
            return int(limit_str[:-2]) * 1024
        else:
            return int(limit_str)

    def _parse_cpu_limit(self, limit_str: str) -> float | None:
        """解析CPU限制字符串"""
        if not limit_str:
            return None

        if limit_str.endswith("%"):
            return float(limit_str[:-1]) / 100.0
        else:
            return float(limit_str)

    def _set_memory_limit(self, pid: int, memory_bytes: int) -> None:
        """设置进程内存限制"""
        import platform

        try:
            system = platform.system().lower()

            if system == "linux":
                # Linux系统使用cgroups设置内存限制
                cgroup_path = f"/sys/fs/cgroup/memory/alon_plugin_{pid}"

                # 创建cgroup
                os.makedirs(cgroup_path, exist_ok=True)

                # 设置内存限制
                with open(f"{cgroup_path}/memory.limit_in_bytes", "w") as f:
                    f.write(str(memory_bytes))

                # 将进程添加到cgroup
                with open(f"{cgroup_path}/cgroup.procs", "w") as f:
                    f.write(str(pid))

                logger.debug(f"已为进程 {pid} 设置内存限制: {memory_bytes} 字节")

            elif system == "darwin":
                # macOS系统内存限制设置
                logger.debug("macOS系统暂不支持进程内存限制设置，将通过监控进行管理")

            else:
                logger.debug(f"系统 {system} 暂不支持内存限制设置")

        except Exception as e:
            logger.debug(f"设置内存限制失败（非关键错误）: {e}")

    def monitor_process_resources(self, pid: int) -> dict[str, Any]:
        """监控进程资源使用情况"""
        try:
            process = psutil.Process(pid)

            # 获取资源使用情况
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()

            # 获取子进程信息
            children = process.children(recursive=True)
            total_memory = memory_info.rss
            total_cpu = cpu_percent

            for child in children:
                try:
                    child_memory = child.memory_info()
                    child_cpu = child.cpu_percent()
                    total_memory += child_memory.rss
                    total_cpu += child_cpu
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # 检查是否超过阈值
            memory_mb = total_memory / 1024 / 1024
            memory_limit_mb = (
                self._parse_memory_limit(plugin_settings.plugin_memory_limit)
                / 1024
                / 1024
            )

            alerts = []
            if memory_limit_mb and memory_mb > memory_limit_mb:
                alerts.append(
                    f"内存使用超限: {memory_mb:.1f}MB > {memory_limit_mb:.1f}MB"
                )

            if total_cpu > plugin_settings.cpu_usage_threshold:
                alerts.append(f"CPU使用过高: {total_cpu:.1f}%")

            return {
                "memory_usage_mb": memory_mb,
                "cpu_usage_percent": total_cpu,
                "child_process_count": len(children),
                "alerts": alerts,
            }

        except psutil.NoSuchProcess:
            return {"error": "进程不存在"}
        except Exception as e:
            return {"error": str(e)}

    def terminate_process_safely(self, pid: int, timeout: int = 30) -> bool:
        """安全地终止进程"""
        try:
            process = psutil.Process(pid)

            # 获取所有子进程
            children = process.children(recursive=True)

            # 先发送SIGTERM信号
            process.terminate()

            # 等待进程退出
            try:
                process.wait(timeout=timeout)
                logger.info(f"进程 {pid} 已正常退出")
                return True
            except psutil.TimeoutExpired:
                # 超时后强制杀死
                logger.warning(f"进程 {pid} 未在 {timeout} 秒内退出，强制杀死")
                process.kill()

                # 杀死所有子进程
                for child in children:
                    try:
                        child.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                return True

        except psutil.NoSuchProcess:
            return True
        except Exception as e:
            logger.error(f"终止进程失败: {e}")
            return False

    def check_network_access(self, host: str, port: int) -> bool:
        """检查网络访问权限"""
        # 始终检查端口是否被禁止（即使没有启用网络隔离）
        if port in self.blocked_ports:
            logger.warning(f"尝试访问被禁止的端口: {port}")
            return False

        # 如果没有启用网络隔离，其他检查跳过
        if not plugin_settings.enable_network_isolation:
            return True

        # 检查主机是否被允许
        if "*" not in plugin_settings.allowed_hosts:
            allowed = any(
                host == allowed_host or host.endswith(f".{allowed_host}")
                for allowed_host in plugin_settings.allowed_hosts
            )
            if not allowed:
                logger.warning(f"尝试访问未被允许的主机: {host}")
                return False

        return True

    def scan_malicious_patterns(
        self, code: str, file_path: str = ""
    ) -> list[dict[str, Any]]:
        """扫描恶意代码模式（增强版）"""
        return self.code_scanner.scan_code(code, file_path)

    def create_sandbox_environment(self, work_dir: Path) -> dict[str, str]:
        """创建沙箱环境变量"""
        sandbox_env = os.environ.copy()

        # 移除敏感环境变量
        sensitive_vars = [
            "HOME",
            "USER",
            "USERNAME",
            "LOGNAME",
            "SSH_AUTH_SOCK",
            "SSH_AGENT_PID",
            "SUDO_USER",
            "SUDO_UID",
            "SUDO_GID",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
        ]

        for var in sensitive_vars:
            sandbox_env.pop(var, None)

        # 设置受限的环境变量
        sandbox_env.update(
            {
                "HOME": str(work_dir),
                "USER": "alon_plugin",
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "PYTHONPATH": str(work_dir),
                "TMPDIR": str(work_dir / "tmp"),
                "ALON_SANDBOX": "true",
            },
        )

        # 创建临时目录
        tmp_dir = work_dir / "tmp"
        tmp_dir.mkdir(exist_ok=True)

        return sandbox_env

    def validate_plugin_permissions(self, plugin_config: dict[str, Any]) -> bool:
        """验证插件权限配置"""
        permissions = plugin_config.get("permissions", {})

        # 检查是否请求了危险权限
        if permissions.get("subprocess_access", False):
            logger.warning("插件请求子进程权限")
            if not plugin_settings.permission_escalation_allowed:
                return False

        # 检查网络访问范围
        if permissions.get("network_access", False):
            allowed_hosts = permissions.get("internet_hosts", [])
            if "*" in allowed_hosts and plugin_settings.strict_security_mode:
                logger.warning("插件请求无限制网络访问")
                return False

        # 检查文件系统访问范围
        file_access = permissions.get("file_system_access", [])
        for path in file_access:
            if any(path.startswith(blocked) for blocked in self.blocked_paths):
                logger.warning(f"插件请求访问被禁止路径: {path}")
                return False

        return True

    def get_security_report(self, plugin_name: str) -> dict[str, Any]:
        """获取安全报告"""
        return {
            "plugin_name": plugin_name,
            "security_level": "high"
            if plugin_settings.strict_security_mode
            else "medium",
            "enabled_features": {
                "code_scanning": plugin_settings.enable_code_scanning,
                "path_traversal_check": plugin_settings.enable_path_traversal_check,
                "network_isolation": plugin_settings.enable_network_isolation,
                "process_isolation": plugin_settings.enable_process_isolation,
                "chroot": plugin_settings.enable_chroot,
            },
            "restrictions": {
                "blocked_directories": list(self.blocked_paths),
                "blocked_ports": list(self.blocked_ports),
                "allowed_extensions": list(self.allowed_extensions),
            },
        }


# 全局安全管理器实例
security_manager = SecurityManager()
