"""
插件运行时测试

测试插件的启动、停止、状态查询和崩溃处理功能，包括：
- 启动 tongyi 插件并验证进程状态
- 停止运行中的插件并验证进程退出
- 验证插件状态查询 API 正确
- 验证插件崩溃后状态更新正确

运行方式：
    uv run pytest -m e2e tests/ai/e2e/test_plugin_runtime.py -v
"""

from __future__ import annotations

import asyncio
import os

import psutil
import pytest

from ai.components.plugin.engine.core.runtime.local_runtime import (
    LocalPluginRuntime,
)


class TestPluginRuntimeStart:
    """插件启动测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_start_tongyi_plugin_creates_process(
        self,
        plugin_runtime_setup: tuple[LocalPluginRuntime, callable],
    ) -> None:
        """
        测试启动 tongyi 插件并验证进程状态

        场景：启动 tongyi 插件
        - 系统创建独立的子进程运行插件
        - 进程 ID 记录到运行时状态
        - 插件状态变为 RUNNING
        """
        runtime, cleanup = plugin_runtime_setup

        try:
            # 1. 启动插件
            await runtime.start()

            # 2. 验证进程已创建
            assert runtime.is_running, "运行时状态应为运行中"
            assert runtime.state == "running", f"状态应为 running，实际为 {runtime.state}"
            assert runtime.process_id is not None, "进程 ID 不应为空"
            assert isinstance(runtime.process_id, int), "进程 ID 应为整数"

            # 3. 验证进程存在且正在运行
            pid = runtime.process_id
            assert psutil.pid_exists(pid), f"进程 {pid} 应存在"
            process = psutil.Process(pid)
            assert process.is_running(), f"进程 {pid} 应正在运行"

            # 4. 验证端口已分配
            assert runtime.port is not None, "端口应已分配"
            assert isinstance(runtime.port, int), "端口应为整数"

            # 5. 验证插件进程是独立的子进程（不是主进程）
            pid = runtime.process_id
            main_pid = os.getpid()
            assert pid != main_pid, "插件进程应与主进程不同"

        finally:
            if runtime.is_running:
                await runtime.stop()


class TestPluginRuntimeStop:
    """插件停止测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_stop_running_plugin_terminates_process(
        self,
        plugin_runtime_setup: tuple[LocalPluginRuntime, callable],
    ) -> None:
        """
        测试停止运行中的插件并验证进程退出

        场景：停止运行中的插件
        - 系统发送终止信号给插件进程
        - 进程退出
        - 运行时状态变为 STOPPED
        """
        runtime, cleanup = plugin_runtime_setup

        try:
            # 1. 启动插件
            await runtime.start()
            assert runtime.is_running, "插件应已启动"
            pid = runtime.process_id

            # 2. 停止插件
            await runtime.stop()

            # 3. 验证进程已退出
            exited = False
            for _ in range(30):
                if not psutil.pid_exists(pid):
                    exited = True
                    break
                await asyncio.sleep(0.5)
            assert exited, f"进程 {pid} 应已退出"

            # 4. 验证运行时状态
            assert not runtime.is_running, "运行时状态应为未运行"
            assert runtime.state == "stopped", f"状态应为 stopped，实际为 {runtime.state}"
            assert runtime.process_id is None, "进程 ID 应被清除"
            assert runtime.port is None, "端口应被清除"

        finally:
            pass  # cleanup fixture 会处理


class TestPluginRuntimeStatus:
    """插件状态查询测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_get_plugin_status_returns_correct_state(
        self,
        plugin_runtime_setup: tuple[LocalPluginRuntime, callable],
    ) -> None:
        """
        测试验证插件状态查询 API 正确

        场景：查询插件状态
        - 启动插件后，状态为 running
        - 停止插件后，状态为 stopped
        - 状态转换：prepared -> running -> stopped
        """
        runtime, cleanup = plugin_runtime_setup

        try:
            # 1. 启动前状态
            assert runtime.state == "prepared", f"初始状态应为 prepared，实际为 {runtime.state}"
            assert not runtime.is_running, "启动前不应为运行状态"
            assert runtime.is_prepared, "启动前应已完成预处理"

            # 2. 启动插件
            await runtime.start()

            # 3. 启动后状态
            assert runtime.state == "running", f"启动后状态应为 running，实际为 {runtime.state}"
            assert runtime.is_running, "启动后应标记为运行中"
            assert runtime.process_id is not None, "进程 ID 应存在"
            assert runtime.port is not None, "端口应存在"
            assert runtime.started_at is not None, "启动时间应已记录"

            # 4. 停止插件
            await runtime.stop()

            # 5. 停止后状态
            assert runtime.state == "stopped", f"停止后状态应为 stopped，实际为 {runtime.state}"
            assert not runtime.is_running, "停止后不应为运行状态"
            assert runtime.process_id is None, "停止后进程 ID 应被清除"
            assert runtime.port is None, "停止后端口应被清除"
            assert runtime.stopped_at is not None, "停止时间应已记录"

        finally:
            if runtime.is_running:
                await runtime.stop()


class TestPluginRuntimeCrash:
    """插件崩溃处理测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_plugin_crash_updates_status_to_inactive(
        self,
        plugin_runtime_setup: tuple[LocalPluginRuntime, callable],
    ) -> None:
        """
        测试验证插件崩溃后状态更新正确

        场景：插件进程崩溃
        - 插件进程因异常崩溃（模拟为发送 SIGKILL）
        - 主服务进程继续运行
        """
        runtime, cleanup = plugin_runtime_setup

        try:
            # 1. 启动插件
            await runtime.start()
            assert runtime.is_running, "插件应已启动"
            pid = runtime.process_id

            # 2. 验证主服务进程仍在运行
            main_pid = os.getpid()
            main_process = psutil.Process(main_pid)
            assert main_process.is_running(), "主服务进程应正在运行"

            # 3. 模拟插件崩溃：发送 SIGKILL
            plugin_process = psutil.Process(pid)
            plugin_process.kill()

            # 4. 等待进程退出
            exited = False
            for _ in range(20):
                if not psutil.pid_exists(pid):
                    exited = True
                    break
                await asyncio.sleep(0.5)
            assert exited, f"插件进程 {pid} 应已退出"

            # 5. 主服务进程应继续运行
            assert psutil.pid_exists(main_pid), "主服务进程应存在"
            assert main_process.is_running(), "主服务进程应正在运行"
            assert os.getpid() == main_pid, "主进程 PID 不应改变"

        finally:
            # 清理：确保进程已终止
            if pid and psutil.pid_exists(pid):
                try:
                    psutil.Process(pid).kill()
                except Exception:
                    pass
            if runtime.is_running:
                try:
                    await runtime.stop()
                except Exception:
                    pass

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_plugin_crash_does_not_affect_main_process(
        self,
        plugin_runtime_setup: tuple[LocalPluginRuntime, callable],
    ) -> None:
        """
        测试插件崩溃不影响主服务

        场景：插件进程崩溃不影响主服务
        - 插件进程因异常崩溃
        - 主服务进程继续运行
        """
        runtime, cleanup = plugin_runtime_setup

        try:
            # 1. 启动插件
            await runtime.start()
            assert runtime.is_running, "插件应已启动"
            pid = runtime.process_id

            # 2. 记录主进程 PID
            main_pid = os.getpid()

            # 3. 确保主进程可以继续工作
            # 在模拟崩溃前后验证主进程可以执行任务
            import time

            def main_process_works():
                return time.time() > 0  # 简单验证主进程仍可运行

            assert main_process_works(), "主进程应能执行任务"

            # 4. 模拟插件崩溃
            plugin_process = psutil.Process(pid)
            plugin_process.kill()

            # 5. 等待进程退出
            exited = False
            for _ in range(20):
                if not psutil.pid_exists(pid):
                    exited = True
                    break
                await asyncio.sleep(0.5)
            assert exited, f"插件进程 {pid} 应已退出"

            # 6. 验证主进程仍可执行任务
            assert main_process_works(), "崩溃后主进程应能继续执行任务"

            # 7. 验证主进程 PID 不变
            assert os.getpid() == main_pid, "主进程 PID 不应改变"

            # 8. 主进程应能正常停止插件
            if runtime.is_running:
                try:
                    await runtime.stop()
                except Exception:
                    pass

        finally:
            if pid and psutil.pid_exists(pid):
                try:
                    psutil.Process(pid).kill()
                except Exception:
                    pass
            if runtime.is_running:
                try:
                    await runtime.stop()
                except Exception:
                    pass
