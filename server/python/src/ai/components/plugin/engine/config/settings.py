"""
配置管理
基于pydantic-settings的配置系统，支持环境变量和配置文件
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # ========== 日志配置 ==========
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str | None = Field(
        default="logs/plugin_engine.log", description="日志文件路径"
    )
    log_rotation: str = Field(default="1 day", description="日志轮转")
    log_retention: str = Field(default="30 days", description="日志保留")

    # ========== 安全模式配置 ==========
    strict_security_mode: bool = Field(default=False, description="启用严格安全模式")
    enable_code_scanning: bool = Field(default=True, description="启用代码扫描")

    # ========== 进程安全限制 ==========
    enable_process_isolation: bool = Field(default=True, description="启用进程隔离")
    enable_chroot: bool = Field(
        default=False, description="启用chroot隔离（需要root权限）"
    )

    # ========== 路径安全配置 ==========
    enable_path_traversal_check: bool = Field(
        default=True, description="启用路径遍历检查"
    )
    allowed_file_extensions: list[str] = Field(
        default=[".py", ".txt", ".json", ".yaml", ".yml", ".md", ".cfg", ".ini"],
        description="允许的文件扩展名",
    )
    blocked_directories: list[str] = Field(
        default=["/etc", "/proc", "/sys", "/dev", "/root", "/home"],
        description="禁止访问的目录",
    )

    # ========== 网络安全配置 ==========
    enable_network_isolation: bool = Field(default=False, description="启用网络隔离")
    allowed_hosts: list[str] = Field(default=["*"], description="允许访问的主机列表")
    blocked_ports: list[int] = Field(
        default=[22, 23, 135, 445], description="禁止访问的端口"
    )

    # ========== 资源监控配置 ==========
    cpu_usage_threshold: float = Field(
        default=80.0, description="CPU使用阈值（百分比）"
    )


# 创建全局配置实例
plugin_settings = Settings()


# 导出配置
__all__ = ["plugin_settings"]
