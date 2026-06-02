"""
辅助函数工具模块
提供各种实用的工具函数
"""

import hashlib
import json
import os
import re
import socket
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def generate_id(prefix: str | None = None) -> str:
    """生成唯一ID"""
    id_str = str(uuid.uuid4())
    if prefix:
        return f"{prefix}{id_str}"
    return id_str


def parse_memory_size(size_str: str) -> int:
    """解析内存大小字符串，返回字节数

    Args:
        size_str: 内存大小字符串，如 "512MB", "1GB"

    Returns:
        字节数
    """
    size_str = size_str.upper().strip()

    # 提取数字部分
    match = re.match(r"^(\d+(?:\.\d+)?)\s*([KMGT]?B?)$", size_str)
    if not match:
        raise ValueError(f"无效的内存大小格式: {size_str}")

    number, unit = match.groups()
    number = float(number)

    # 转换单位
    multipliers = {
        "B": 1,
        "K": 1024,
        "KB": 1024,
        "M": 1024**2,
        "MB": 1024**2,
        "G": 1024**3,
        "GB": 1024**3,
        "T": 1024**4,
        "TB": 1024**4,
    }

    return int(number * multipliers.get(unit, 1))


def parse_cpu_percent(cpu_str: str) -> float:
    """解析CPU百分比字符串

    Args:
        cpu_str: CPU百分比字符串，如 "50%", "0.5", "100"

    Returns:
        CPU百分比值
    """
    if not cpu_str:
        raise ValueError("CPU百分比字符串不能为空")

    cpu_str = cpu_str.strip()

    if cpu_str.endswith("%"):
        value = float(cpu_str[:-1])
    else:
        value = float(cpu_str)
        # 如果值在0-1之间，假设是小数形式，转换为百分比
        if 0 <= value <= 1:
            value = value * 100

    # 验证范围
    if value < 0 or value > 100:
        raise ValueError(f"CPU百分比必须在0-100之间，得到: {value}")

    return value


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """安全的JSON解析

    Args:
        json_str: JSON字符串
        default: 解析失败时的默认值

    Returns:
        解析结果或默认值
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def validate_plugin_name(name: str) -> bool:
    """验证插件名称是否合法

    Args:
        name: 插件名称

    Returns:
        是否合法
    """
    if not name or not isinstance(name, str):
        return False
    # 插件名称只能包含小写字母、数字、下划线、短横线
    # 长度在1-128个字符之间，与Go版本保持一致
    pattern = r"^[a-z0-9_-]{1,128}$"
    return bool(re.match(pattern, name))


def validate_plugin_id(plugin_id: str) -> bool:
    """验证插件ID是否合法

    Args:
        plugin_id: 插件ID

    Returns:
        是否合法
    """
    if not plugin_id or not isinstance(plugin_id, str):
        return False
    # 插件ID可以包含字母、数字、下划线、短横线和点
    # 长度在3-100个字符之间，支持包名格式如 com.example.plugin
    pattern = r"^[a-zA-Z0-9._-]{3,100}$"
    return bool(re.match(pattern, plugin_id))


def create_secure_hash(data: str, algorithm: str = "sha256") -> str:
    """创建安全哈希值

    Args:
        data: 要哈希的数据
        algorithm: 哈希算法

    Returns:
        哈希值
    """
    hash_func = getattr(hashlib, algorithm)
    return hash_func(data.encode("utf-8")).hexdigest()


def format_bytes(bytes_value: int) -> str:
    """格式化字节数为可读字符串

    Args:
        bytes_value: 字节数

    Returns:
        格式化后的字符串
    """
    if bytes_value == 0:
        return "0 B"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            if unit == "B":
                return f"{int(bytes_value)} {unit}"
            else:
                return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def ensure_directory(path: str | Path) -> Path:
    """确保目录存在

    Args:
        path: 目录路径

    Returns:
        目录路径
    """
    if isinstance(path, str):
        path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    if not filename:
        return "file"

    if filename is None:
        return "file"

    # 转换为小写
    cleaned = filename.lower()
    # 替换空格为下划线
    cleaned = cleaned.replace(" ", "_")
    # 移除不安全字符，包括@#$%等特殊字符，每个字符替换为一个下划线
    cleaned = re.sub(r'[<>:"/\\|?*@#$%]', "_", cleaned)
    # 处理连续的点，保留单个点
    cleaned = re.sub(r"\.{2,}", ".", cleaned)

    return cleaned.strip("_")


def merge_configs(
    base_config: dict[str, Any], override_config: dict[str, Any]
) -> dict[str, Any]:
    """合并配置字典

    Args:
        base_config: 基础配置
        override_config: 覆盖配置

    Returns:
        合并后的配置
    """
    result = base_config.copy()

    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def get_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """计算文件哈希值

    Args:
        file_path: 文件路径
        algorithm: 哈希算法

    Returns:
        文件哈希值
    """
    hash_func = getattr(hashlib, algorithm)()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def is_port_available(port: int, host: str = "localhost") -> bool:
    """检查端口是否可用

    Args:
        port: 端口号
        host: 主机地址

    Returns:
        端口是否可用
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0
    except Exception:
        return False


def find_available_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("localhost", port))
                return port
        except OSError:
            continue

    raise RuntimeError(
        f"无法在 {start_port}-{start_port + max_attempts} 范围内找到可用端口"
    )


def format_error_response(
    message: str, code: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """格式化错误响应

    Args:
        message: 错误消息
        code: 错误代码
        details: 错误详情

    Returns:
        格式化的错误响应
    """
    error_response = {
        "error": {
            "message": message,
            "code": code,
            "timestamp": datetime.now().isoformat(),
        }
    }

    if details:
        error_response["error"]["details"] = details

    return error_response


def parse_plugin_manifest(manifest_data: dict[str, Any]) -> dict[str, Any]:
    """解析插件清单

    Args:
        manifest_data: 插件清单数据

    Returns:
        解析后的清单数据

    Raises:
        ValueError: 如果清单数据无效
    """
    required_fields = ["name", "version", "description", "author", "type"]

    for field in required_fields:
        if field not in manifest_data:
            raise ValueError(f"插件清单缺少必需字段: {field}")

    # 简单验证
    if not manifest_data["name"]:
        raise ValueError("插件名称不能为空")

    if not manifest_data["version"]:
        raise ValueError("插件版本不能为空")

    return manifest_data.copy()


def sanitize_filename(filename: str) -> str:
    """清理文件名，兼容 clean_filename 功能

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 替换空格为下划线
    cleaned = filename.replace(" ", "_")
    # 替换路径分隔符为下划线
    cleaned = cleaned.replace("/", "_").replace("\\", "_")
    # 移除其他不安全字符
    cleaned = re.sub(r'[<>:"|?*]', "_", cleaned)
    # 移除多余的下划线
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_")


def check_file_permissions(file_path: str, mode: str) -> bool:
    """检查文件权限

    Args:
        file_path: 文件路径
        mode: 权限模式 ('r', 'w', 'x')

    Returns:
        是否有指定权限
    """
    try:
        if not os.path.exists(file_path):
            return False

        if mode == "r":
            return os.access(file_path, os.R_OK)
        elif mode == "w":
            return os.access(file_path, os.W_OK)
        elif mode == "x":
            return os.access(file_path, os.X_OK)
        else:
            return False
    except Exception:
        return False


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """计算文件哈希，兼容 get_file_hash 功能

    Args:
        file_path: 文件路径
        algorithm: 哈希算法

    Returns:
        文件哈希值
    """
    return get_file_hash(Path(file_path), algorithm)


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小，兼容 format_bytes 功能

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的字符串
    """
    return format_bytes(size_bytes)


def format_time_duration(seconds: int) -> str:
    """格式化时间间隔

    Args:
        seconds: 秒数

    Returns:
        格式化后的时间字符串
    """
    if seconds == 0:
        return "0 seconds"

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if secs > 0:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")

    return " ".join(parts)


def json_response_helper(
    data: Any, status: str = "success", success: bool | None = None
) -> dict[str, Any]:
    """JSON响应助手

    Args:
        data: 响应数据
        status: 响应状态
        success: 成功标志（可选）

    Returns:
        格式化的JSON响应
    """
    response = {"status": status, "data": data, "timestamp": datetime.now().isoformat()}

    # 如果显式指定了success参数
    if success is not None:
        response["success"] = success
    # 默认情况下，根据status判断success
    else:
        response["success"] = status == "success"

    return response
