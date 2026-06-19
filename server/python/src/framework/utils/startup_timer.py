"""启动计时器，用于记录和输出启动阶段耗时"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import time

from framework.utils.log_util import (
    Color,
    format_timestamp,
    write_empty_line,
    write_separator,
)


@dataclass
class PhaseInfo:
    """阶段信息"""

    name: str
    duration: float = 0.0
    details: dict[str, str] = field(default_factory=dict)
    order: int | None = None


class StartupTimer:
    """启动计时器，用于记录和输出启动阶段耗时"""

    def __init__(self, app_name: str = "应用"):
        self.app_name = app_name
        self.start_time = time()
        self.phases: list[PhaseInfo] = []

    @contextmanager
    def phase(self, name: str, order: int | None = None) -> Iterator[PhaseInfo]:
        """阶段计时上下文管理器"""
        phase_info = PhaseInfo(name=name, order=order)
        phase_start = time()
        try:
            yield phase_info
        finally:
            phase_info.duration = time() - phase_start
            self.phases.append(phase_info)

    def print_summary(
        self,
        modules: list[str] | None = None,
        address: str | None = None,
        docs_path: str | None = None,
        extra_info: dict[str, str] | None = None,
    ) -> None:
        """打印启动完成摘要"""
        total_duration = time() - self.start_time

        write_empty_line()
        write_separator()
        print(f"{Color.GREEN}{self.app_name} 启动完成！{Color.RESET}")
        print(f"{Color.CYAN}总启动耗时:{Color.RESET} {total_duration:.3f} 秒")
        print(f"{Color.CYAN}启动阶段耗时:{Color.RESET}")

        ordered_phases = sorted(
            enumerate(self.phases),
            key=lambda item: item[1].order if item[1].order is not None else item[0],
        )
        for i, (_, phase) in enumerate(ordered_phases, 1):
            # 将详情压缩到一行显示
            if phase.details:
                details_str = ", ".join(f"{k}={v}" for k, v in phase.details.items())
                print(f"  阶段{i} ({phase.name}): {phase.duration:.3f}秒 | {details_str}")
            else:
                print(f"  阶段{i} ({phase.name}): {phase.duration:.3f}秒")

        print(f"{Color.CYAN}完成时间:{Color.RESET} {format_timestamp()}")

        if modules:
            # 模块列表压缩到一行显示
            modules_str = ", ".join(modules)
            print(f"{Color.CYAN}🔌 已加载模块:{Color.RESET} {len(modules)} 个 [{modules_str}]")

        if extra_info:
            for key, value in extra_info.items():
                print(f"{Color.CYAN}{key}:{Color.RESET} {value}")

        if address:
            print()
            print(f"{Color.GREEN}访问地址:{Color.RESET} {address}")
            if docs_path:
                print(f"{Color.GREEN}API 文档:{Color.RESET} {address}{docs_path}")

        write_separator()
        write_empty_line()
