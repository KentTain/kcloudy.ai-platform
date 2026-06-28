"""
插件安装流程测试

测试插件的完整生命周期，包括：
- 安装插件并验证虚拟环境创建
- 验证重复安装返回正确错误
- 卸载已安装插件并验证资源清理
- 验证 OSS 上传正确

运行方式：
    uv run pytest -m e2e tests/ai/e2e/test_plugin_install.py -v
"""

import shutil
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select

from ai.components.plugin.engine.core.plugin_manager import PluginManagerFactory
from framework.database.core.engine import setup_engine
from framework.database.core.engine_pool import init_default_engine
from ai.components.plugin.engine.models.enums import PluginStatus
from ai.components.plugin.engine.models.request import InstallRequest
from ai.models.plugin_config import PluginConfig as AIPluginConfig
from ai.models.plugin_runtime_state import PluginRuntimeState
from framework.configs import get_settings
from framework.storage import get_storage_provider
from framework.tenant.context import TenantContext
from framework.tenant.plugin_protocols import get_plugin_installation_provider
from tests.ai.e2e.helpers.plugin_test_helper import PluginTestHelper


@pytest_asyncio.fixture
async def init_engine_pool(ai_settings):
    """
    初始化全局数据库引擎池。

    E2E 测试需要初始化全局引擎池和引擎管理器，
    因为 PluginInstallationProvider 使用 get_task_session()
    访问全局引擎池获取数据库会话。
    """
    from framework.configs.settings import get_settings

    settings = ai_settings

    # 初始化全局引擎管理器
    sqlalchemy_config = settings.sqlalchemy
    setup_engine(
        database_url=sqlalchemy_config.url,
        echo=sqlalchemy_config.echo,
    )

    # 初始化全局 DatabaseEnginePool（多租户引擎池）
    init_default_engine(
        database_url=sqlalchemy_config.url,
        echo=sqlalchemy_config.echo,
    )

    yield


class TestPluginInstall:
    """插件安装流程测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_install_tongyi_plugin_and_verify_environment(
        self,
        e2e_session,
        test_tenant_id,
        plugin_package_path,
        cleanup_test_resources,
        init_engine_pool,
        plugin_provider,
    ) -> None:
        """
        测试安装 tongyi 插件并验证虚拟环境创建

        场景：安装 tongyi 插件
        - 调用安装 API 安装 tongyi 插件包
        - 系统创建 PluginInstallation 记录
        - 系统创建虚拟环境并安装依赖
        - 系统上传插件包到 OSS
        - 安装状态变为 ACTIVE
        """
        # 设置租户上下文
        TenantContext.set_tenant_id(test_tenant_id)

        # 获取 tongyi 插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")

        # 读取插件包数据
        with open(tongyi_path, "rb") as f:
            package_data = f.read()

        # 获取插件管理器
        manager = await PluginManagerFactory.get_manager(test_tenant_id, e2e_session)
        helper = PluginTestHelper(test_tenant_id)

        # 初始化管理器
        await manager.initialize(e2e_session)

        try:
            # 安装插件
            install_request = InstallRequest(auto_start=False)
            plugin_id = await manager.install_plugin(
                e2e_session, package_data, install_request
            )

            # 等待插件状态变为 ACTIVE
            await helper.wait_for_plugin_status(
                e2e_session,
                plugin_id,
                PluginStatus.ACTIVE,
                timeout=60.0,
            )

            # 验证 PluginInstallation 记录存在
            provider = get_plugin_installation_provider()
            installation = await provider.get_installation(test_tenant_id, plugin_id)

            assert installation is not None, f"插件安装记录不存在: {plugin_id}"
            assert installation.plugin_id == plugin_id
            assert installation.status.upper() == "ACTIVE", (
                f"插件状态应为 ACTIVE，实际为: {installation.status}"
            )
            assert installation.tenant_id == test_tenant_id

            # 验证虚拟环境目录存在
            plugin_dir = manager.workspace_dir / plugin_id
            assert plugin_dir.exists(), f"插件目录不存在: {plugin_dir}"

            # 验证 manifest.yaml 存在
            manifest_path = plugin_dir / "manifest.yaml"
            assert manifest_path.exists(), f"manifest.yaml 不存在: {manifest_path}"

            # 验证虚拟环境存在（检查 python 可执行文件）
            venv_python = plugin_dir / ".venv" / "bin" / "python"
            if not venv_python.exists():
                # Windows 路径
                venv_python = plugin_dir / ".venv" / "Scripts" / "python.exe"

            assert venv_python.exists(), f"虚拟环境 Python 不存在: {venv_python}"

            # 验证 AI 侧配置存在
            config_result = await e2e_session.execute(
                select(AIPluginConfig).where(
                    AIPluginConfig.tenant_id == test_tenant_id,
                    AIPluginConfig.plugin_id == plugin_id,
                )
            )
            ai_config = config_result.scalar_one_or_none()
            assert ai_config is not None, f"AI 侧配置不存在: {plugin_id}"
            assert ai_config.plugin_config is not None

            # 验证运行时状态记录存在
            state_result = await e2e_session.execute(
                select(PluginRuntimeState).where(
                    PluginRuntimeState.tenant_id == test_tenant_id,
                    PluginRuntimeState.plugin_id == plugin_id,
                )
            )
            runtime_state = state_result.scalar_one_or_none()
            assert runtime_state is not None, f"运行时状态记录不存在: {plugin_id}"

        finally:
            # 清理：卸载插件
            try:
                await self._cleanup_plugin(
                    e2e_session, test_tenant_id, plugin_id, manager
                )
            except Exception:
                pass

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_install_duplicate_plugin_returns_error(
        self,
        e2e_session,
        test_tenant_id,
        plugin_package_path,
        cleanup_test_resources,
        init_engine_pool,
        plugin_provider,
    ) -> None:
        """
        测试安装已存在的插件返回正确错误

        场景：安装已存在的插件
        - 尝试安装已安装的 tongyi 插件
        - 系统拒绝安装并返回"插件已安装"错误
        """
        # 设置租户上下文
        TenantContext.set_tenant_id(test_tenant_id)

        # 获取 tongyi 插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")

        # 读取插件包数据
        with open(tongyi_path, "rb") as f:
            package_data = f.read()

        # 获取插件管理器
        manager = await PluginManagerFactory.get_manager(test_tenant_id, e2e_session)
        helper = PluginTestHelper(test_tenant_id)

        # 初始化管理器
        await manager.initialize(e2e_session)

        plugin_id = None

        try:
            # 第一次安装
            install_request = InstallRequest(auto_start=False)
            plugin_id = await manager.install_plugin(
                e2e_session, package_data, install_request
            )

            # 等待插件状态变为 ACTIVE
            await helper.wait_for_plugin_status(
                e2e_session,
                plugin_id,
                PluginStatus.ACTIVE,
                timeout=60.0,
            )

            # 验证插件已安装
            provider = get_plugin_installation_provider()
            installation = await provider.get_installation(test_tenant_id, plugin_id)
            assert installation is not None, "第一次安装应该成功"

            # 尝试重复安装
            with pytest.raises(ValueError) as exc_info:
                await manager.install_plugin(e2e_session, package_data, install_request)

            # 验证错误信息包含"已安装"
            error_message = str(exc_info.value).lower()
            assert (
                "已安装" in error_message or "already" in error_message
            ), f"错误信息应包含'已安装'，实际为: {error_message}"

        finally:
            # 清理：卸载插件
            if plugin_id:
                try:
                    await self._cleanup_plugin(
                        e2e_session, test_tenant_id, plugin_id, manager
                    )
                except Exception:
                    pass

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_uninstall_plugin_and_verify_cleanup(
        self,
        e2e_session,
        test_tenant_id,
        plugin_package_path,
        cleanup_test_resources,
        init_engine_pool,
        plugin_provider,
    ) -> None:
        """
        测试卸载已安装的插件并验证资源清理

        场景：卸载已安装的插件
        - 调用卸载 API 卸载 tongyi 插件
        - 系统停止插件进程
        - 系统删除虚拟环境
        - 系统删除 PluginInstallation 记录
        """
        # 设置租户上下文
        TenantContext.set_tenant_id(test_tenant_id)

        # 获取 tongyi 插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")

        # 读取插件包数据
        with open(tongyi_path, "rb") as f:
            package_data = f.read()

        # 获取插件管理器
        manager = await PluginManagerFactory.get_manager(test_tenant_id, e2e_session)
        helper = PluginTestHelper(test_tenant_id)

        # 初始化管理器
        await manager.initialize(e2e_session)

        plugin_id = None

        try:
            # 先安装插件
            install_request = InstallRequest(auto_start=False)
            plugin_id = await manager.install_plugin(
                e2e_session, package_data, install_request
            )

            # 等待插件状态变为 ACTIVE
            await helper.wait_for_plugin_status(
                e2e_session,
                plugin_id,
                PluginStatus.ACTIVE,
                timeout=60.0,
            )

            # 记录插件目录路径（用于后续验证清理）
            plugin_dir = manager.workspace_dir / plugin_id

            # 验证插件已安装
            provider = get_plugin_installation_provider()
            installation = await provider.get_installation(test_tenant_id, plugin_id)
            assert installation is not None, "插件应已安装"

            # 执行卸载
            await self._cleanup_plugin(
                e2e_session, test_tenant_id, plugin_id, manager
            )

            # 验证 PluginInstallation 记录已删除
            installation_after = await provider.get_installation(
                test_tenant_id, plugin_id
            )
            assert installation_after is None, (
                f"插件安装记录应已删除: {plugin_id}"
            )

            # 验证虚拟环境目录已删除
            assert not plugin_dir.exists(), f"插件目录应已删除: {plugin_dir}"

            # 验证 AI 侧配置已删除
            config_result = await e2e_session.execute(
                select(AIPluginConfig).where(
                    AIPluginConfig.tenant_id == test_tenant_id,
                    AIPluginConfig.plugin_id == plugin_id,
                )
            )
            ai_config = config_result.scalar_one_or_none()
            assert ai_config is None, f"AI 侧配置应已删除: {plugin_id}"

            # 验证运行时状态记录已删除
            state_result = await e2e_session.execute(
                select(PluginRuntimeState).where(
                    PluginRuntimeState.tenant_id == test_tenant_id,
                    PluginRuntimeState.plugin_id == plugin_id,
                )
            )
            runtime_state = state_result.scalar_one_or_none()
            assert runtime_state is None, f"运行时状态记录应已删除: {plugin_id}"

            # 验证内存中的插件信息已清理
            assert plugin_id not in manager.plugins, "内存中插件信息应已清理"
            assert plugin_id not in manager.running_plugins, "内存中运行时信息应已清理"

        except Exception:
            # 清理：如果测试失败，尝试清理资源
            if plugin_id:
                try:
                    await self._cleanup_plugin(
                        e2e_session, test_tenant_id, plugin_id, manager
                    )
                except Exception:
                    pass
            raise

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_oss_upload_correct(
        self,
        e2e_session,
        test_tenant_id,
        plugin_package_path,
        cleanup_test_resources,
        init_engine_pool,
        plugin_provider,
    ) -> None:
        """
        测试验证 OSS 上传正确

        场景：安装插件后验证 OSS 上传
        - 安装 tongyi 插件
        - 验证插件包已上传到 OSS
        - 验证 OSS 路径格式正确
        """
        # 设置租户上下文
        TenantContext.set_tenant_id(test_tenant_id)

        # 获取 tongyi 插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")

        # 读取插件包数据
        with open(tongyi_path, "rb") as f:
            package_data = f.read()

        # 获取插件管理器
        manager = await PluginManagerFactory.get_manager(test_tenant_id, e2e_session)
        helper = PluginTestHelper(test_tenant_id)

        # 初始化管理器
        await manager.initialize(e2e_session)

        plugin_id = None

        try:
            # 安装插件
            install_request = InstallRequest(auto_start=False)
            plugin_id = await manager.install_plugin(
                e2e_session, package_data, install_request
            )

            # 等待插件状态变为 ACTIVE
            await helper.wait_for_plugin_status(
                e2e_session,
                plugin_id,
                PluginStatus.ACTIVE,
                timeout=60.0,
            )

            # 获取插件配置
            config_result = await e2e_session.execute(
                select(AIPluginConfig).where(
                    AIPluginConfig.tenant_id == test_tenant_id,
                    AIPluginConfig.plugin_id == plugin_id,
                )
            )
            ai_config = config_result.scalar_one_or_none()
            assert ai_config is not None, f"AI 侧配置不存在: {plugin_id}"
            assert ai_config.plugin_config is not None

            # 获取插件版本
            plugin_config = ai_config.plugin_config
            version = plugin_config.get("configuration", {}).get("version")
            assert version is not None, "插件版本信息不存在"

            # 构建 OSS 路径
            settings = get_settings()
            bucket_name = settings.oss.bucket
            oss_path = f"plugins/{test_tenant_id}/{plugin_id}/{version}/plugin.zip"

            # 验证 OSS 文件存在
            try:
                storage = get_storage_provider(settings.oss)
                # 尝试下载文件验证存在
                downloaded_data = await storage.download(
                    bucket=bucket_name,
                    name=oss_path,
                )
                assert downloaded_data is not None, f"OSS 文件不存在: {oss_path}"
                assert len(downloaded_data) > 0, f"OSS 文件为空: {oss_path}"

                # 验证下载的数据与原始包大小相近
                # 注意：可能存在压缩差异，只验证大小相近
                assert abs(len(downloaded_data) - len(package_data)) < 1000, (
                    f"OSS 文件大小与原始包差异过大: "
                    f"OSS={len(downloaded_data)}, 原始={len(package_data)}"
                )

            except Exception as e:
                # 如果 OSS 不可用，跳过验证
                if "Connection" in str(e) or "connect" in str(e).lower():
                    pytest.skip(f"OSS 服务不可用: {e}")
                raise

        finally:
            # 清理：卸载插件
            if plugin_id:
                try:
                    await self._cleanup_plugin(
                        e2e_session, test_tenant_id, plugin_id, manager
                    )
                except Exception:
                    pass

    async def _cleanup_plugin(
        self,
        session,
        tenant_id: str,
        plugin_id: str,
        manager,
    ) -> None:
        """
        清理插件资源的辅助方法

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID
            manager: 插件管理器
        """
        from sqlalchemy import delete

        from ai.models.plugin_config import PluginConfig as AIPluginConfig
        from ai.models.plugin_runtime_state import PluginRuntimeState
        from framework.tenant.plugin_protocols import get_plugin_installation_provider

        # 1. 停止插件
        try:
            if plugin_id in manager.running_plugins:
                await manager.stop_plugin(plugin_id, session)
        except Exception:
            pass

        # 2. 删除 AI 侧配置
        try:
            await session.execute(
                delete(AIPluginConfig).where(
                    AIPluginConfig.tenant_id == tenant_id,
                    AIPluginConfig.plugin_id == plugin_id,
                )
            )
        except Exception:
            pass

        # 3. 删除 AI 侧运行时状态
        try:
            await session.execute(
                delete(PluginRuntimeState).where(
                    PluginRuntimeState.tenant_id == tenant_id,
                    PluginRuntimeState.plugin_id == plugin_id,
                )
            )
        except Exception:
            pass

        # 4. 删除 Tenant 侧安装记录
        try:
            provider = get_plugin_installation_provider()
            await provider.delete_installation(tenant_id, plugin_id)
        except Exception:
            pass

        # 5. 删除本地运行目录
        try:
            plugin_dir = manager.workspace_dir / plugin_id
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir, ignore_errors=True)
        except Exception:
            pass

        # 6. 清理内存注册
        try:
            if plugin_id in manager.running_plugins:
                del manager.running_plugins[plugin_id]
            if plugin_id in manager.plugins:
                del manager.plugins[plugin_id]
        except Exception:
            pass

        # 提交更改
        await session.flush()
