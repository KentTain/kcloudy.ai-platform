"""启动计时器，用于记录和输出启动阶段耗时"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from time import time
from typing import Iterator


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

        print("\n" + "=" * 60)
        print(f"{self.app_name} 启动完成！")
        print(f"总启动耗时: {total_duration:.3f} 秒")
        print("启动阶段耗时:")

        ordered_phases = sorted(
            enumerate(self.phases),
            key=lambda item: item[1].order if item[1].order is not None else item[0],
        )
        for i, (_, phase) in enumerate(ordered_phases, 1):
            print(f"  阶段{i} ({phase.name}): {phase.duration:.3f}秒")
            if phase.details:
                for key, value in phase.details.items():
                    print(f"    - {key}: {value}")

        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if modules:
            print(f"🔌 已加载模块: {len(modules)} 个")
            for name in modules:
                print(f"   - {name}")

        if extra_info:
            for key, value in extra_info.items():
                print(f"{key}: {value}")

        if address:
            print(f"\n访问地址: {address}")
            if docs_path:
                print(f"API 文档: {address}{docs_path}")

        print("=" * 60 + "\n")
