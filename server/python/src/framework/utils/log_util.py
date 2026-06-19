"""
控制台日志工具

提供带颜色和图标的日志输出方法，参照 PowerShell tool_util.ps1 实现。
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import TextIO


# ANSI 颜色代码
class Color:
    """ANSI 颜色常量"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


# 图标常量
class Icon:
    """日志图标"""

    INFO = "💡"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    STEP = "▶"
    MODULE = "🔌"


def _ensure_utf8():
    """确保控制台支持 UTF-8"""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
            sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, OSError):
            pass


_ensure_utf8()


def write_log(
    level: str,
    message: str,
    icon: str,
    color: str,
    file: TextIO | None = None,
) -> None:
    """
    内部日志打印函数

    Args:
        level: 日志级别
        message: 日志消息
        icon: 日志图标
        color: 颜色代码
        file: 输出流，默认 stdout
    """
    output = file or sys.stdout
    print(f"{color}{icon} [{level}]{Color.RESET}: {message}", file=output)


def write_info(message: str) -> None:
    """
    打印信息日志

    Args:
        message: 日志消息
    """
    write_log("INFO", message, Icon.INFO, Color.CYAN)


def write_success(message: str) -> None:
    """
    打印成功日志

    Args:
        message: 日志消息
    """
    write_log("SUCCESS", message, Icon.SUCCESS, Color.GREEN)


def write_warning(message: str) -> None:
    """
    打印警告日志

    Args:
        message: 日志消息
    """
    write_log("WARNING", message, Icon.WARNING, Color.YELLOW)


def write_error(message: str, file: TextIO | None = None) -> None:
    """
    打印错误日志

    Args:
        message: 日志消息
        file: 输出流，默认 stderr
    """
    output = file or sys.stderr
    write_log("ERROR", message, Icon.ERROR, Color.RED, file=output)


def write_separator(char: str = "=", length: int = 60, color: str = Color.WHITE) -> None:
    """
    打印分隔线

    Args:
        char: 分隔符字符
        length: 分隔线长度
        color: 颜色代码
    """
    print(f"{color}{char * length}{Color.RESET}")


def write_title(title: str, subtitle: str = "") -> None:
    """
    打印标题

    Args:
        title: 标题文本
        subtitle: 副标题文本
    """
    write_separator()
    print(f"{Color.WHITE}  {title}{Color.RESET}")
    if subtitle:
        print(f"{Color.GRAY}  {subtitle}{Color.RESET}")
    write_separator()


def write_step_header(
    step_number: int,
    title: str,
    total_steps: int = 0,
) -> None:
    """
    显示步骤标题

    Args:
        step_number: 步骤编号
        title: 步骤标题
        total_steps: 总步骤数（可选）
    """
    print()
    write_separator()
    if total_steps > 0:
        print(f"{Color.WHITE}  Step {step_number}/{total_steps}: {title}{Color.RESET}")
    else:
        print(f"{Color.WHITE}  Step {step_number}: {title}{Color.RESET}")
    write_separator()


def write_empty_line(count: int = 1) -> None:
    """
    打印空行

    Args:
        count: 空行数量
    """
    for _ in range(count):
        print()


def write_completion_message(
    title: str = "Complete!",
    subtitle: str = "",
    sections: list[dict] | None = None,
    address: str | None = None,
    docs_path: str | None = None,
    modules: list[str] | None = None,
    extra_info: dict[str, str] | None = None,
    total_duration: float | None = None,
) -> None:
    """
    显示完成消息

    Args:
        title: 主标题
        subtitle: 副标题
        sections: 消息节数组，每个元素为包含 title、messages、color 的字典
        address: 访问地址
        docs_path: API 文档路径
        modules: 已加载模块列表
        extra_info: 额外信息
        total_duration: 总耗时（秒）
    """
    write_empty_line()
    write_title(title, subtitle)
    write_empty_line()

    if total_duration is not None:
        print(f"{Color.CYAN}总启动耗时:{Color.RESET} {total_duration:.3f} 秒")

    if sections:
        for section in sections:
            section_title = section.get("title", "Information")
            section_messages = section.get("messages", [])
            section_color = section.get("color", Color.CYAN)

            print(f"{section_color}{section_title}:{Color.RESET}")
            for msg in section_messages:
                print(f"  {msg}")
            write_empty_line()

    if modules:
        print(f"{Color.CYAN}{Icon.MODULE} 已加载模块:{Color.RESET} {len(modules)} 个")
        for name in modules:
            print(f"   - {name}")
        write_empty_line()

    if extra_info:
        for key, value in extra_info.items():
            print(f"{Color.CYAN}{key}:{Color.RESET} {value}")
        write_empty_line()

    if address:
        print(f"{Color.GREEN}访问地址:{Color.RESET} {address}")
        if docs_path:
            print(f"{Color.GREEN}API 文档:{Color.RESET} {address}{docs_path}")
        write_empty_line()


def format_timestamp() -> str:
    """格式化当前时间戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
