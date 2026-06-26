"""
插件测试辅助工具类

提供 E2E 测试中常用的插件操作辅助方法，简化测试代码编写。
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from ai.components.plugin.engine.core.plugin_manager import (
    PluginManagerFactory,
    TenantPluginManager,
)
from ai.components.plugin.engine.models.enums import PluginStatus
from framework.tenant.plugin_protocols import get_plugin_installation_provider

if TYPE_CHECKING:
    from ai.components.plugin.engine.models.plugin import PluginInfo


class PluginTestHelper:
    """
    插件测试辅助工具类

    封装常用测试操作，提供：
    - 轮询等待插件状态
    - 断言插件安装成功
    - 断言插件运行正常
    - 安全清理插件资源

    使用示例:
        helper = PluginTestHelper(tenant_id="test-tenant")

        # 等待插件状态
        await helper.wait_for_plugin_status(
            session=session,
            plugin_id="tongyi",
            target_status=PluginStatus.ACTIVE,
            timeout=30
        )

        # 断言安装成功
        await helper.assert_plugin_installed(session, "tongyi")

        # 断言运行正常
        await helper.assert_plugin_running(session, "tongyi")

        # 清理资源
        await helper.cleanup_plugin(session, "tongyi")
    """

    def __init__(self, tenant_id: str):
        """
        初始化插件测试辅助工具

        Args:
            tenant_id: 租户 ID
        """
        self.tenant_id = tenant_id
        self._manager: TenantPluginManager | None = None

    async def get_manager(self, session: AsyncSession) -> TenantPluginManager:
        """
        获取插件管理器实例

        Args:
            session: 数据库会话

        Returns:
            TenantPluginManager: 插件管理器实例
        """
        if self._manager is None:
            self._manager = await PluginManagerFactory.get_manager(
                self.tenant_id, session
            )
        return self._manager

    async def wait_for_plugin_status(
        self,
        session: AsyncSession,
        plugin_id: str,
        target_status: PluginStatus | str,
        timeout: float = 30.0,
        poll_interval: float = 0.5,
    ) -> bool:
        """
        轮询等待插件达到指定状态

        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            target_status: 目标状态（PluginStatus 枚举或字符串）
            timeout: 超时时间（秒），默认 30 秒
            poll_interval: 轮询间隔（秒），默认 0.5 秒

        Returns:
            bool: 是否在超时前达到目标状态

        Raises:
            TimeoutError: 超时未达到目标状态
        """
        # 标准化目标状态
        if isinstance(target_status, PluginStatus):
            target = target_status.value
        else:
            target = target_status.lower()

        manager = await self.get_manager(session)
        elapsed = 0.0

        while elapsed < timeout:
            # 检查内存中的插件状态
            if plugin_id in manager.plugins:
                plugin_info = manager.plugins[plugin_id]
                current_status = plugin_info.status
                if current_status and current_status.lower() == target:
                    return True

            # 检查数据库中的安装状态
            try:
                provider = get_plugin_installation_provider()
                installation = await provider.get_installation(
                    self.tenant_id, plugin_id
                )
                if installation and installation.status.lower() == target:
                    return True
            except Exception:
                pass  # 忽略查询错误，继续轮询

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(
            f"等待插件状态超时: plugin_id={plugin_id}, "
            f"target_status={target}, timeout={timeout}s"
        )

    async def assert_plugin_installed(
        self,
        session: AsyncSession,
        plugin_id: str,
        check_database: bool = True,
    ) -> dict:
        """
        验证插件安装成功

        自动检查安装状态和数据库记录。

        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            check_database: 是否检查数据库记录，默认 True

        Returns:
            dict: 插件信息，包含 id, status, name 等

        Raises:
            AssertionError: 插件未安装或状态异常
        """
        manager = await self.get_manager(session)

        # 检查内存中的插件信息
        assert plugin_id in manager.plugins, (
            f"插件未安装: plugin_id={plugin_id}, tenant_id={self.tenant_id}"
        )

        plugin_info = manager.plugins[plugin_id]

        # 检查数据库记录
        if check_database:
            provider = get_plugin_installation_provider()
            installation = await provider.get_installation(self.tenant_id, plugin_id)

            assert installation is not None, (
                f"插件安装记录不存在: plugin_id={plugin_id}, "
                f"tenant_id={self.tenant_id}"
            )

            assert installation.status.upper() in ("ACTIVE", "INACTIVE"), (
                f"插件安装状态异常: plugin_id={plugin_id}, "
                f"status={installation.status}"
            )

        return {
            "id": plugin_info.id,
            "name": plugin_info.name,
            "version": plugin_info.version,
            "status": plugin_info.status,
        }

    async def assert_plugin_running(
        self,
        session: AsyncSession,
        plugin_id: str,
        check_process: bool = True,
    ) -> dict:
        """
        验证插件进程运行正常

        检查进程存在且状态为 ACTIVE。

        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            check_process: 是否检查进程存在，默认 True

        Returns:
            dict: 运行时信息，包含 pid, port, status 等

        Raises:
            AssertionError: 插件未运行或进程不存在
        """
        manager = await self.get_manager(session)

        # 检查运行时存在
        assert plugin_id in manager.running_plugins, (
            f"插件未运行: plugin_id={plugin_id}, tenant_id={self.tenant_id}"
        )

        runtime = manager.running_plugins[plugin_id]
        plugin_info = manager.plugins.get(plugin_id)

        # 构建运行时信息
        runtime_info = {
            "plugin_id": plugin_id,
            "status": "active",
        }

        # 获取进程信息（使用 process_id）
        if runtime.process_id:
            runtime_info["pid"] = runtime.process_id

        # 获取端口信息
        if runtime.port:
            runtime_info["port"] = runtime.port

        # 从 plugin_info 补充信息
        if plugin_info:
            if "port" not in runtime_info and plugin_info.port:
                runtime_info["port"] = plugin_info.port
            if "pid" not in runtime_info and plugin_info.pid:
                runtime_info["pid"] = plugin_info.pid

        # 检查进程存在
        if check_process and "pid" in runtime_info:
            import psutil

            pid = runtime_info["pid"]
            assert psutil.pid_exists(pid), (
                f"插件进程不存在: plugin_id={plugin_id}, pid={pid}"
            )

        # 验证数据库状态
        provider = get_plugin_installation_provider()
        installation = await provider.get_installation(self.tenant_id, plugin_id)

        assert installation is not None, (
            f"插件安装记录不存在: plugin_id={plugin_id}"
        )

        assert installation.status.upper() == "ACTIVE", (
            f"插件状态不是 ACTIVE: plugin_id={plugin_id}, "
            f"status={installation.status}"
        )

        return runtime_info

    async def cleanup_plugin(
        self,
        session: AsyncSession,
        plugin_id: str,
        force: bool = False,
    ) -> bool:
        """
        安全清理插件资源

        停止插件进程并清理相关资源。

        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            force: 是否强制清理（即使停止失败也继续），默认 False

        Returns:
            bool: 是否清理成功

        Raises:
            RuntimeError: 清理失败且 force=False
        """
        manager = await self.get_manager(session)
        errors: list[str] = []

        # 1. 停止运行中的插件
        if plugin_id in manager.running_plugins:
            try:
                success = await manager.stop_plugin(plugin_id, session)
                if not success:
                    errors.append(f"停止插件失败: {plugin_id}")
            except Exception as e:
                errors.append(f"停止插件异常: {plugin_id}, error={e}")

        # 2. 清理内存中的插件信息
        if plugin_id in manager.plugins:
            try:
                del manager.plugins[plugin_id]
            except Exception as e:
                errors.append(f"清理插件信息异常: {e}")

        # 3. 清理数据库记录（可选）
        # 注意：这里不自动删除安装记录，由测试自行决定

        if errors:
            error_msg = "; ".join(errors)
            if force:
                # 强制模式：记录错误但不抛出异常
                import logging
                logging.getLogger(__name__).warning(
                    f"强制清理插件完成，但存在错误: {error_msg}"
                )
                return False
            else:
                raise RuntimeError(f"清理插件失败: {error_msg}")

        return True

    async def install_plugin_from_path(
        self,
        session: AsyncSession,
        package_path: str,
        auto_start: bool = False,
    ) -> str:
        """
        从路径安装插件

        便捷方法，封装插件安装流程。

        Args:
            session: 数据库会话
            package_path: 插件包路径
            auto_start: 是否自动启动，默认 False

        Returns:
            str: 安装成功的插件 ID

        Raises:
            FileNotFoundError: 插件包不存在
            RuntimeError: 安装失败
        """
        import pathlib

        path = pathlib.Path(package_path)
        if not path.exists():
            raise FileNotFoundError(f"插件包不存在: {package_path}")

        # 读取插件包
        with open(path, "rb") as f:
            package_data = f.read()

        # 创建安装请求
        from ai.components.plugin.engine.models.request import InstallRequest

        install_request = InstallRequest(auto_start=auto_start)

        # 安装插件
        manager = await self.get_manager(session)
        plugin_id = await manager.install_plugin(session, package_data, install_request)

        return plugin_id

    async def get_plugin_info(
        self,
        session: AsyncSession,
        plugin_id: str,
    ) -> PluginInfo | None:
        """
        获取插件信息

        Args:
            session: 数据库会话
            plugin_id: 插件 ID

        Returns:
            PluginInfo | None: 插件信息，不存在则返回 None
        """
        manager = await self.get_manager(session)
        return manager.plugins.get(plugin_id)

    async def is_plugin_running(
        self,
        session: AsyncSession,
        plugin_id: str,
    ) -> bool:
        """
        检查插件是否正在运行

        Args:
            session: 数据库会话
            plugin_id: 插件 ID

        Returns:
            bool: 是否正在运行
        """
        manager = await self.get_manager(session)
        return plugin_id in manager.running_plugins

    async def get_all_plugins(
        self,
        session: AsyncSession,
    ) -> dict[str, PluginInfo]:
        """
        获取所有已安装的插件

        Args:
            session: 数据库会话

        Returns:
            dict[str, PluginInfo]: 插件 ID 到插件信息的映射
        """
        manager = await self.get_manager(session)
        return manager.plugins.copy()

    async def get_running_plugins(
        self,
        session: AsyncSession,
    ) -> list[str]:
        """
        获取所有正在运行的插件 ID 列表

        Args:
            session: 数据库会话

        Returns:
            list[str]: 运行中的插件 ID 列表
        """
        manager = await self.get_manager(session)
        return list(manager.running_plugins.keys())
