"""
插件管理器核心模块
负责插件的生命周期管理、租户隔离、运行时管理等
"""

import asyncio
import hashlib
import json
import os
import shutil
import tempfile
import time
import zipfile
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil  # 添加用于系统监控
import yaml
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.components.plugin.engine.core.communication.protocol import PluginError
from ai.components.plugin.engine.core.helper import (
    PluginConfig,
    PluginConfigProcessor,
)
from ai.components.plugin.engine.core.monitoring.monitoring import (
    PluginPerformanceMonitor,
)
from ai.components.plugin.engine.core.runtime.base import PluginRuntime
from ai.components.plugin.engine.core.runtime.factory import RuntimeFactory
from ai.components.plugin.engine.core.security.security import SecurityManager
from ai.components.plugin.engine.core.session.session_manager import SessionManager
from ai.components.plugin.engine.core.warmup.plugin_warmup_manager import (
    PluginCandidate,
    PluginWarmupManager,
    PluginWarmupResult,
    WarmupConfig,
    WarmupExecutionResult,
    WarmupStatus,
    WarmupStatusInfo,
)
from ai.components.plugin.engine.models.enums import (
    PluginStatus,
    RuntimeType,
    SourceType,
)
from ai.components.plugin.engine.models.enums import PluginType as DBPluginType
from ai.components.plugin.engine.models.plugin import PluginInfo
from ai.components.plugin.engine.models.request import InstallRequest
from ai.components.plugin.engine.utils.logger import get_logger
from ai.models.plugin_config import PluginConfig as AIPluginConfig
from ai.models.plugin_runtime_state import PluginRuntimeState
from ai_plugin.server.core.entities.plugin.setup import PluginAsset
from framework.configs.settings import settings
from framework.storage import get_storage_provider
from framework.tenant.plugin_protocols import (
    PluginInstallationDTO,
    get_plugin_installation_provider,
)

logger = get_logger(__name__)


@dataclass
class PluginAssetFile:
    """插件资源文件信息"""

    relative_path: str  # 相对于_assets目录的路径
    content: bytes  # 文件内容
    file_size: int  # 文件大小
    content_type: str  # 文件MIME类型
    file_hash: str  # 文件SHA256哈希值

    @classmethod
    def from_file_path(cls, file_path: Path, base_path: Path) -> "PluginAssetFile":
        """从文件路径创建PluginAssetFile对象"""
        with open(file_path, "rb") as f:
            content = f.read()

        relative_path = str(file_path.relative_to(base_path))
        file_size = len(content)
        file_hash = hashlib.sha256(content).hexdigest()

        # 简单的MIME类型判断
        suffix = file_path.suffix.lower()
        content_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".json": "application/json",
            ".yaml": "application/x-yaml",
            ".yml": "application/x-yaml",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".css": "text/css",
            ".js": "application/javascript",
            ".html": "text/html",
        }
        content_type = content_type_map.get(suffix, "application/octet-stream")

        return cls(
            relative_path=relative_path,
            content=content,
            file_size=file_size,
            content_type=content_type,
            file_hash=file_hash,
        )


@dataclass
class PluginPackageInfo:
    """插件包信息，包含配置和资源文件"""

    config: PluginConfig  # 插件配置
    assets: list[PluginAsset]  # 资源文件列表
    package_hash: str  # 插件包SHA256哈希值

    @property
    def has_assets(self) -> bool:
        """是否包含资源文件"""
        return len(self.assets) > 0


class TenantPluginManager:
    """租户级插件管理器 - 支持租户隔离的插件管理"""

    def __init__(self, tenant_id: str):
        """
        初始化租户插件管理器

        Args:
            tenant_id: 租户ID
        """

        self._initialized = False
        self.tenant_id = tenant_id
        self.logger = get_logger(f"plugin_manager_{tenant_id}")

        # 插件注册表 - 维护当前租户的所有插件状态信息
        self.plugins: dict[
            str, PluginInfo
        ] = {}  # 内存中的插件信息 (plugin_id -> PluginInfo)
        self.running_plugins: dict[
            str, PluginRuntime
        ] = {}  # 当前运行中的插件实例 (plugin_id -> PluginRuntime)

        # 插件启动锁 - 防止并发启动同一个插件
        self._plugin_start_locks: dict[str, asyncio.Lock] = {}

        # 插件准备状态缓存 - 避免重复的数据库查询和文件检查
        # key: plugin_id, value: 缓存插件准备状态的时间戳
        self._plugin_ready_cache: dict[str, float] = {}
        self._plugin_ready_cache_ttl = 60  # 缓存有效期60秒

        # 核心组件初始化
        self.session_manager = SessionManager()  # 负责插件调用会话的管理
        self.security_manager = SecurityManager()  # 负责插件的安全权限控制
        self.performance_monitor = PluginPerformanceMonitor()  # 性能监控器
        self.warmup_manager = PluginWarmupManager(
            self, self.performance_monitor
        )  # 预热管理器
        self.runtime_factory = RuntimeFactory()  # 插件运行时工厂

        # 插件运行目录
        self.tenant_plugin_dir = settings.plugin.plugin_base_dir / "tenants" / tenant_id
        self.workspace_dir = self.tenant_plugin_dir / "runtime"  # 插件运行时工作目录
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # OSS配置
        self.oss_bucket_name = settings.oss.bucket  # OSS bucket名称
        self.oss_base_path = f"plugins/{tenant_id}"

        self.logger.info(f"租户插件管理器初始化完成: {tenant_id}")

    async def initialize(self, session: AsyncSession):
        """初始化插件管理器"""
        if self._initialized:
            return

        self.logger.info("正在初始化插件管理器...")

        # 从数据库加载插件元数据（不启动插件）
        await self._load_plugins_metadata_from_database(session)

        # 执行启动时预热
        try:
            warmup_result = await self.warmup_manager.startup_warmup(session)
            if warmup_result.status == WarmupStatus.COMPLETED:
                warmed_count = len(warmup_result.warmed_plugins)
                self.logger.info(f"启动时预热完成: {warmed_count} 个插件已预热")
        except Exception:
            self.logger.exception("启动时预热失败，但不影响系统正常运行")

        self._initialized = True
        self.logger.info(
            f"插件管理器初始化完成，发现 {len(self.plugins)} 个插件（懒加载模式）"
        )

    async def _load_plugins_metadata_from_database(self, session: AsyncSession):
        """从数据库加载已安装的插件元数据"""
        self.logger.info(f"从数据库加载租户插件元数据: {self.tenant_id}")

        provider = get_plugin_installation_provider()
        installations = await provider.get_tenant_installations(self.tenant_id)

        loaded_count = 0
        for installation_dto in installations:
            try:
                # 查询 AI 侧配置和运行时状态
                config_result = await session.execute(
                    select(AIPluginConfig).where(
                        AIPluginConfig.tenant_id == self.tenant_id,
                        AIPluginConfig.plugin_id == installation_dto.plugin_id,
                    )
                )
                ai_config = config_result.scalar_one_or_none()

                state_result = await session.execute(
                    select(PluginRuntimeState).where(
                        PluginRuntimeState.tenant_id == self.tenant_id,
                        PluginRuntimeState.plugin_id == installation_dto.plugin_id,
                    )
                )
                runtime_state = state_result.scalar_one_or_none()

                # 组装 PluginInfo
                plugin_info = PluginInfo(
                    id=installation_dto.plugin_id,
                    status=installation_dto.status,
                    installed_at=None,  # DTO 中没有 installed_at
                )
                if ai_config and ai_config.plugin_config:
                    plugin_info.config = ai_config.plugin_config

                self.plugins[installation_dto.plugin_id] = plugin_info
                loaded_count += 1
            except Exception as e:
                self.logger.exception(
                    f"加载插件元数据失败 {installation_dto.plugin_id}"
                )

        self.logger.info(f"从数据库加载插件元数据完成: {loaded_count} 个插件")

    async def _load_plugin_info_from_installation(
        self, config: dict | None, status: str | None = None
    ) -> PluginInfo | None:
        """从配置字典加载插件信息（不依赖本地文件）"""
        try:
            if not config:
                self.logger.warning(f"插件配置为空")
                return None

            plugin_info = PluginInfo(
                status=status,
            )
            plugin_info.config = config

            return plugin_info

        except Exception:
            self.logger.exception(f"从数据库加载插件信息失败")
            return None

    async def _load_plugin_config(
        self, config_path: Path
    ) -> tuple[PluginConfig, list[PluginAsset]]:
        """加载插件配置文件"""

        processor = PluginConfigProcessor(plugin_dir=config_path.parent)
        processor.parse_plugin_config()
        return processor.get_plugin_config(), processor.files

    async def _get_plugin_start_lock(self, plugin_id: str) -> asyncio.Lock:
        """获取插件启动锁"""
        if plugin_id not in self._plugin_start_locks:
            self._plugin_start_locks[plugin_id] = asyncio.Lock()
        return self._plugin_start_locks[plugin_id]

    async def _upload_plugin_to_oss(
        self, plugin_id: str, version: str, plugin_package: bytes
    ) -> str:
        """上传插件包到OSS（包含版本号）"""
        try:
            # 构建OSS路径 - 包含版本号避免覆盖
            oss_path = f"{self.oss_base_path}/{plugin_id}/{version}/plugin.zip"

            # 获取存储提供者
            storage = get_storage_provider(settings.oss)

            # 上传到OSS
            await storage.upload(
                bucket=self.oss_bucket_name,
                name=oss_path,
                data=plugin_package,
            )

            self.logger.info(f"插件包已上传到OSS: {oss_path}")
            return oss_path

        except Exception as e:
            self.logger.exception(f"上传插件包到OSS失败: {plugin_id}@{version}")
            raise ValueError(f"上传插件包到OSS失败: {e}")

    async def _download_plugin_from_oss(self, plugin_id: str, version: str) -> bytes:
        """从OSS下载插件包（包含版本号）"""
        try:
            # 构建OSS路径 - 包含版本号
            oss_path = f"{self.oss_base_path}/{plugin_id}/{version}/plugin.zip"

            # 获取存储提供者
            storage = get_storage_provider(settings.oss)

            # 从OSS下载
            plugin_data = await storage.download(
                bucket=self.oss_bucket_name,
                name=oss_path,
            )

            self.logger.info(f"插件包已从OSS下载: {oss_path}")
            return plugin_data

        except Exception as e:
            self.logger.exception(f"从OSS下载插件包失败: {plugin_id}@{version}")
            raise ValueError(f"从OSS下载插件包失败: {e}")

    async def _upload_plugin_assets_to_oss(
        self,
        plugin_id: str,
        version: str,
        assets: list[PluginAsset],
    ) -> dict[str, str]:
        """将插件_assets文件上传到OSS，返回上传结果映射"""
        if not assets:
            self.logger.info(f"插件 {plugin_id} 无_assets文件需要上传")
            return {}

        uploaded_files = {}
        failed_files = []

        self.logger.info(
            f"开始上传插件_assets文件: {plugin_id}@{version} ({len(assets)} 个文件)"
        )

        for asset in assets:
            try:
                # 构建OSS路径：plugins/{tenant_id}/{plugin_id}/{version}/assets/{relative_path}
                oss_path = f"{self.oss_base_path}/{plugin_id}/{version}/assets/{asset.filename}"

                # 获取存储提供者
                storage = get_storage_provider(settings.oss)

                # 上传到OSS
                await storage.upload(
                    bucket=self.oss_bucket_name,
                    name=oss_path,
                    data=asset.data,
                )

                uploaded_files[asset.filename] = oss_path
                self.logger.debug(f"资源文件已上传: {asset.filename} -> {oss_path}")

            except Exception:
                failed_files.append(asset.filename)
                self.logger.exception(f"上传资源文件异常: {asset.filename}")

        if failed_files:
            self.logger.warning(f"部分资源文件上传失败: {failed_files}")
            # 目前记录警告但不中断安装流程

        self.logger.info(
            f"插件_assets文件上传完成: {plugin_id}@{version} (成功: {len(uploaded_files)}, 失败: {len(failed_files)})",
        )

        return uploaded_files

    async def _download_plugin_asset_from_oss(
        self, plugin_id: str, version: str, asset_path: str
    ) -> bytes | None:
        """从OSS下载指定的插件资源文件"""
        try:
            # 构建OSS路径
            oss_path = f"{self.oss_base_path}/{plugin_id}/{version}/assets/{asset_path}"

            # 获取存储提供者
            storage = get_storage_provider(settings.oss)

            # 从OSS下载
            content = await storage.download(
                bucket=self.oss_bucket_name,
                name=oss_path,
            )

            self.logger.debug(f"从OSS下载资源文件成功: {oss_path}")
            return content

        except Exception:
            self.logger.exception(
                f"从OSS下载资源文件异常: {plugin_id}@{version}/{asset_path}"
            )
            return None

    async def _check_duplicate_installation(
        self, session: AsyncSession, plugin_config: PluginConfig
    ) -> None:
        """检查是否已经安装了相同或不同版本的插件"""
        plugin_id = (
            f"{plugin_config.configuration.author}/{plugin_config.configuration.name}"
        )

        provider = get_plugin_installation_provider()
        existing = await provider.get_installation(self.tenant_id, plugin_id)
        if existing:
            raise ValueError(f"插件 {plugin_id} 已安装")
        return None

    async def _ensure_plugin_ready(
        self, session: AsyncSession, plugin_id: str, use_cache: bool = True
    ) -> bool:
        """
        确保插件准备就绪

        :param session: 数据库会话
        :param plugin_id: 插件ID
        :param use_cache: 是否使用缓存，默认True
        :return: 插件是否准备就绪
        """
        # 检查缓存（注意，因为加了缓存，如果服务器的其他节点更新了缓存，或者插件被卸载了，此处会有60秒的延迟，因为缓存过期时间就是60秒）
        if use_cache and plugin_id in self._plugin_ready_cache:
            cached_time = self._plugin_ready_cache[plugin_id]
            current_time = time.time()

            # 如果缓存未过期，直接返回
            if current_time - cached_time < self._plugin_ready_cache_ttl:
                self.logger.debug(
                    f"使用缓存的插件准备状态 plugin_id={plugin_id}, 缓存时长={current_time - cached_time:.2f}秒",
                )
                # 即使有缓存，也要检查插件是否仍在运行
                if plugin_id in self.running_plugins:
                    return True
                else:
                    # 如果插件不在运行中，清除缓存，需要重新准备
                    self.logger.warning(
                        f"插件准备状态缓存存在但插件未运行 plugin_id={plugin_id}, 清除缓存"
                    )
                    del self._plugin_ready_cache[plugin_id]
            else:
                self.logger.debug(
                    f"插件准备状态缓存已过期 plugin_id={plugin_id}, 重新准备"
                )
        else:
            if not use_cache:
                self.logger.debug(f"强制刷新插件准备状态 plugin_id={plugin_id}")
            else:
                self.logger.debug(
                    f"没有缓存的插件准备状态 plugin_id={plugin_id}, 重新准备"
                )

        # 获取插件启动锁，防止并发
        lock = await self._get_plugin_start_lock(plugin_id)

        plugin_dir = self.workspace_dir / plugin_id

        async with lock:
            # 检查数据库中的插件状态 (通过 Provider)
            provider = get_plugin_installation_provider()
            installation_dto = await provider.get_installation(
                self.tenant_id, plugin_id
            )

            if not installation_dto:
                # 检查插件是否已经在运行
                if plugin_id in self.running_plugins:
                    # 如果插件在运行，但是数据库中不存在，则说明插件被卸载了，需要停止该插件
                    self.logger.warning(
                        f"插件已在运行: {plugin_id}, 但是数据库中不存在，需要停止该插件"
                    )
                    await self.stop_plugin(plugin_id, session)
                    # 删除插件目录
                    if plugin_dir.exists():
                        shutil.rmtree(plugin_dir)

                raise ValueError(f"插件不存在: {plugin_id}")

            # 查询 AI 侧配置
            config_result = await session.execute(
                select(AIPluginConfig).where(
                    AIPluginConfig.tenant_id == self.tenant_id,
                    AIPluginConfig.plugin_id == plugin_id,
                )
            )
            ai_config = config_result.scalar_one_or_none()

            # 从数据库加载插件配置
            plugin_info = await self._load_plugin_info_from_installation(
                ai_config.plugin_config if ai_config else None,
                installation_dto.status,
            )
            if not plugin_info:
                raise ValueError(f"无法加载插件配置: {plugin_id}")

            config_dict = ai_config.plugin_config if ai_config else {}

            if plugin_id in self.plugins:
                # 如果插件已经在内存中，则检查版本是否一致，有可能插件升级了，需要停止旧版本
                old_plugin_info = self.plugins[plugin_id]
                old_version = (
                    old_plugin_info.config.get("configuration", {}).get("version")
                    if hasattr(old_plugin_info, "config") and old_plugin_info.config
                    else None
                )
                new_version = config_dict.get("configuration", {}).get("version")
                if old_version and new_version and old_version != new_version:
                    self.logger.warning(
                        f"插件版本不一致: {plugin_id}，旧版本: {old_version}，新版本: {new_version}",
                    )
                    await self.stop_plugin(plugin_id, session)
                    # 删除插件目录
                    if plugin_dir.exists():
                        shutil.rmtree(plugin_dir)

            # 注册到内存, 不管之前是否存在，都注册到内存，确保插件信息是最新的
            self.plugins[plugin_id] = plugin_info

            # 检查本地插件文件是否存在

            manifest_path = plugin_dir / "manifest.yaml"

            if not manifest_path.exists():
                self.logger.info(f"本地插件文件不存在，从OSS下载: {plugin_id}")

                if not config_dict:
                    raise ValueError(f"插件配置不存在: {plugin_id}")

                # 获取版本信息
                plugin_version = config_dict.get("configuration", {}).get("version")

                if not plugin_version:
                    raise ValueError(f"插件版本信息不存在: {plugin_id}")

                # 从OSS下载插件包
                plugin_package = await self._download_plugin_from_oss(
                    plugin_id, plugin_version
                )

                # 安装插件文件到本地
                await self._install_plugin_files(plugin_id, plugin_package)

                self.logger.info(f"已从OSS恢复插件文件: {plugin_id}")

            # 更新插件准备状态缓存 - 避免重复的数据库查询和文件检查
            self._plugin_ready_cache[plugin_id] = time.time()

            # 检查插件是否已经在运行,如果已经在运行，则直接返回True
            if plugin_id in self.running_plugins:
                self.logger.debug(f"插件已在运行: {plugin_id}")
                return True

            # 启动插件
            result = await self._start_plugin_internal(plugin_id)

            # 5.6: 启动成功后更新 PluginRuntimeState
            if result:
                try:
                    state_result = await session.execute(
                        select(PluginRuntimeState).where(
                            PluginRuntimeState.tenant_id == self.tenant_id,
                            PluginRuntimeState.plugin_id == plugin_id,
                        )
                    )
                    runtime_state_record = state_result.scalar_one_or_none()
                    if runtime_state_record:
                        runtime_state_record.status = "active"
                        if plugin_id in self.running_plugins:
                            runtime_inst = self.running_plugins[plugin_id]
                            if runtime_inst.process_id:
                                runtime_state_record.process_id = (
                                    runtime_inst.process_id
                                )
                            if runtime_inst.port:
                                runtime_state_record.port = runtime_inst.port
                        runtime_state_record.last_started_at = datetime.now()
                        await session.flush()
                        self.logger.debug(f"已更新插件运行时状态: {plugin_id}")
                except Exception:
                    self.logger.exception(f"更新插件运行时状态失败: {plugin_id}")

            return result

    async def _start_plugin_internal(self, plugin_id: str) -> bool:
        """内部插件启动方法"""
        if plugin_id not in self.plugins:
            raise ValueError(f"插件不存在: {plugin_id}")

        plugin_info = self.plugins[plugin_id]
        self.logger.info(f"启动插件: {plugin_id}")

        startup_start_time = time.time()  # 记录启动开始时间

        try:
            # 创建运行时
            runtime = await self.runtime_factory.create_runtime(
                plugin_info=plugin_info,
                workspace_dir=self.workspace_dir / plugin_id,
            )

            # 检查是否已完成预处理
            if not runtime.is_prepared:
                self.logger.info(f"插件预处理: {plugin_id}")
                await runtime.prepare()

            # 启动插件
            await runtime.start()

            # 注册运行时
            self.running_plugins[plugin_id] = runtime

            # 记录启动时间
            startup_time = time.time() - startup_start_time
            self.performance_monitor.record_startup_time(plugin_id, startup_time)

            # 初始记录资源使用情况
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                self.performance_monitor.record_resource_usage(
                    plugin_id, memory_mb, cpu_percent
                )
            except:
                pass  # 忽略资源监控错误

            self.logger.info(f"插件启动成功: {plugin_id} (用时: {startup_time:.3f}秒)")
            return True

        except Exception:
            startup_time = time.time() - startup_start_time
            self.performance_monitor.record_startup_time(
                plugin_id, startup_time
            )  # 记录失败的启动时间
            self.logger.exception(
                f"插件启动失败 {plugin_id} (用时: {startup_time:.3f}秒)"
            )
            return False

    async def install_plugin(
        self,
        session: AsyncSession,
        plugin_package: bytes,
        install_request: InstallRequest | None = None,
    ) -> str:
        """安装插件"""
        self.logger.info("开始安装插件")

        #  第一阶段：解析插件包（包含_assets提取）
        package_info = await self._parse_plugin_package(plugin_package)
        plugin_config = package_info.config

        #  第二阶段：验证插件
        await self._validate_plugin(plugin_config)

        #  第三阶段：检查重复安装
        await self._check_duplicate_installation(session, plugin_config)

        # 生成插件ID
        plugin_id = (
            f"{plugin_config.configuration.author}/{plugin_config.configuration.name}"
        )

        try:
            # 下面的步骤如果出错了，需要回滚

            #  第四阶段：本地安装插件文件
            self.logger.info(f"开始准备插件文件: {plugin_id}")
            await self._install_plugin_files(plugin_id, plugin_package)

            #  第五阶段：创建运行时并执行重量级预处理
            plugin_info = PluginInfo(config=plugin_config, installed_at=datetime.now())

            runtime = await self.runtime_factory.create_runtime(
                plugin_info, self.workspace_dir / plugin_id
            )

            self.logger.info(f"开始插件重量级预处理: {plugin_id}")
            await runtime.prepare()  #  这里执行所有重量级操作
            self.logger.info(f"插件预处理完成: {plugin_id}")

            #  第六阶段：本地安装成功后，上传插件包和_assets到OSS
            self.logger.info(f"本地安装成功，开始上传到OSS: {plugin_id}")

            # 上传插件包
            oss_path = await self._upload_plugin_to_oss(
                plugin_id, plugin_config.configuration.version, plugin_package
            )

            # 上传_assets文件
            assets_upload_result = await self._upload_plugin_assets_to_oss(
                plugin_id=plugin_id,
                version=plugin_config.configuration.version,
                assets=package_info.assets,
            )

            #  第七阶段：注册插件到数据库和内存
            install_info = {
                "oss_path": oss_path,
                "version": plugin_config.configuration.version,
                "package_hash": package_info.package_hash,
                "assets_count": len(package_info.assets),
                "assets_upload_result": assets_upload_result,
            }
            config_override = install_request.config_override if install_request else {}
            await self._register_plugin_installation(
                session,
                plugin_config,
                plugin_id,
                install_info,
                install_request.auto_start if install_request else False,
                config_override,
            )

            #  第八阶段：如果需要自动启动
            if install_request and install_request.auto_start:
                self.logger.info(f"自动启动插件: {plugin_id}")
                # await self.start_plugin(plugin_id) ## 不自动启动插件了，主要是性能考虑，延迟到调用阶段启动

            self.logger.info(
                f"插件安装成功: {plugin_id}@{plugin_config.configuration.version} (包含 {len(package_info.assets)} 个资源文件)",
            )
            return plugin_id

        except Exception:
            self.logger.exception("插件安装失败，开始执行完整回滚...")

            # 执行完整的回滚操作
            try:
                await self._rollback_failed_installation(
                    session,
                    plugin_config if "plugin_config" in locals() else None,
                    plugin_id if "plugin_id" in locals() else None,
                    oss_path if "oss_path" in locals() else None,
                )
            except Exception:
                self.logger.exception("回滚操作失败")

            raise

    async def _rollback_failed_installation(
        self,
        session: AsyncSession,
        plugin_config: PluginConfig | None,
        plugin_id: str | None,
        oss_path: str | None,
    ):
        """执行失败安装的完整回滚操作"""
        self.logger.info("开始执行安装失败回滚操作...")
        rollback_steps = []

        try:
            # 1. 清理本地安装文件
            if plugin_config and plugin_id:
                plugin_dir = self.workspace_dir / plugin_id
                if plugin_dir.exists():
                    shutil.rmtree(plugin_dir, ignore_errors=True)
                    rollback_steps.append(f"清理本地文件: {plugin_dir}")
                    self.logger.info(f" 已清理本地安装文件: {plugin_dir}")

            # 2. 从内存中移除插件
            if plugin_id and plugin_id in self.plugins:
                del self.plugins[plugin_id]
                rollback_steps.append(f"从内存移除插件: {plugin_id}")
                self.logger.info(f" 已从内存移除插件: {plugin_id}")

            # 3. 删除数据库记录
            if plugin_id:
                try:
                    deleted_count = await self._delete_plugin_installation(
                        session, plugin_id
                    )
                    if deleted_count > 0:
                        rollback_steps.append(f"删除数据库记录: {plugin_id}")
                        self.logger.info(f" 已删除数据库记录: {plugin_id}")
                except Exception as e:
                    self.logger.warning(f"删除数据库记录失败: {e}")

            # 4. 删除OSS中的插件包
            if oss_path:
                try:
                    storage = get_storage_provider(settings.oss)
                    success = await storage.delete(
                        bucket=self.oss_bucket_name,
                        name=oss_path,
                    )
                    if success:
                        rollback_steps.append(f"删除OSS文件: {oss_path}")
                        self.logger.info(f" 已删除OSS插件包: {oss_path}")
                    else:
                        self.logger.warning(f"删除OSS插件包失败: {oss_path}")
                except Exception as e:
                    self.logger.warning(f"删除OSS插件包异常: {e}")

            self.logger.info(
                f"回滚操作完成，执行了 {len(rollback_steps)} 个步骤: {rollback_steps}"
            )

        except Exception as e:
            raise e

    async def _delete_plugin_installation(
        self, session: AsyncSession, plugin_id: str
    ) -> int:
        """删除插件安装记录"""
        provider = get_plugin_installation_provider()
        deleted_count = 0

        # 删除 AI 侧配置和运行时状态
        try:
            config_result = await session.execute(
                select(AIPluginConfig).where(
                    AIPluginConfig.tenant_id == self.tenant_id,
                    AIPluginConfig.plugin_id == plugin_id,
                )
            )
            ai_config = config_result.scalar_one_or_none()
            if ai_config:
                await session.delete(ai_config)
                deleted_count += 1

            state_result = await session.execute(
                select(PluginRuntimeState).where(
                    PluginRuntimeState.tenant_id == self.tenant_id,
                    PluginRuntimeState.plugin_id == plugin_id,
                )
            )
            runtime_state = state_result.scalar_one_or_none()
            if runtime_state:
                await session.delete(runtime_state)

            await session.flush()
        except Exception:
            self.logger.exception(f"删除 AI 侧插件记录失败: {plugin_id}")

        # 删除 Tenant 侧安装记录
        try:
            await provider.delete_installation(self.tenant_id, plugin_id)
            deleted_count += 1
        except ValueError:
            self.logger.warning(f"安装记录不存在: {plugin_id}")

        return deleted_count

    async def start_plugin(self, plugin_id: str) -> bool:
        """启动插件（公共接口）"""
        return await self._start_plugin_internal(plugin_id)

    async def _update_plugin_last_accessed(self, session: AsyncSession, plugin_id: str):
        """更新插件最后访问时间（更新 AI 侧运行时状态）"""
        try:
            # 更新 AI 侧的 plugin_runtime_states 表
            result = await session.execute(
                select(PluginRuntimeState).where(
                    and_(
                        PluginRuntimeState.tenant_id == self.tenant_id,
                        PluginRuntimeState.plugin_id == plugin_id,
                    ),
                ),
            )
            runtime_state = result.scalar_one_or_none()

            if runtime_state:
                runtime_state.last_accessed_at = datetime.now()
                runtime_state.call_count = (runtime_state.call_count or 0) + 1
                await session.flush()
                self.logger.debug(f"已更新插件访问时间: {plugin_id}")

        except Exception:
            self.logger.exception(f"更新插件访问时间失败: {plugin_id}")
            # 不抛出异常，因为这不是关键功能

    async def _update_plugin_running_by_installation(
        self, session: AsyncSession, plugin_id: str
    ):
        """更新插件运行状态（通过 Provider 更新 Tenant 侧 + AI 侧运行时状态）"""
        try:
            # 1. 通过 Provider 更新 Tenant 侧状态为 ACTIVE
            provider = get_plugin_installation_provider()
            await provider.update_installation(
                self.tenant_id, plugin_id, {"status": "ACTIVE"}
            )
            self.logger.debug(f"已通过 Provider 更新插件状态为 ACTIVE: {plugin_id}")

            # 2. 更新 AI 侧的 plugin_runtime_states 表
            result = await session.execute(
                select(PluginRuntimeState).where(
                    and_(
                        PluginRuntimeState.tenant_id == self.tenant_id,
                        PluginRuntimeState.plugin_id == plugin_id,
                    ),
                ),
            )
            runtime_state = result.scalar_one_or_none()

            if runtime_state:
                runtime_state.status = "active"
                runtime_state.last_started_at = datetime.now()
                await session.flush()
                self.logger.debug(f"已更新插件运行时状态: {plugin_id}")
            else:
                self.logger.warning(f"未找到插件运行时状态记录: {plugin_id}")

        except Exception:
            self.logger.exception(f"更新插件运行状态失败: {plugin_id}")
            # 不抛出异常，因为这不是关键功能

    async def stop_plugin(
        self, plugin_id: str, session: AsyncSession | None = None
    ) -> bool:
        """停止插件"""
        if plugin_id not in self.running_plugins:
            self.logger.warning(f"插件未运行: {plugin_id}")
            return False

        runtime = self.running_plugins[plugin_id]
        self.logger.info(f"停止插件: {plugin_id}")

        try:
            # 停止运行时
            await runtime.stop()

            # 移除运行时
            del self.running_plugins[plugin_id]

            # 清除插件准备状态缓存
            if plugin_id in self._plugin_ready_cache:
                del self._plugin_ready_cache[plugin_id]
                self.logger.debug(f"已清除插件准备状态缓存: {plugin_id}")

            # 5.7: 停止后更新 PluginRuntimeState
            if session:
                try:
                    state_result = await session.execute(
                        select(PluginRuntimeState).where(
                            PluginRuntimeState.tenant_id == self.tenant_id,
                            PluginRuntimeState.plugin_id == plugin_id,
                        )
                    )
                    runtime_state_record = state_result.scalar_one_or_none()
                    if runtime_state_record:
                        runtime_state_record.status = "inactive"
                        runtime_state_record.last_stopped_at = datetime.now()
                        await session.flush()
                        self.logger.debug(f"已更新插件运行时状态: {plugin_id}")
                except Exception:
                    self.logger.exception(f"更新插件运行时状态失败: {plugin_id}")

            self.logger.info(f"插件停止成功: {plugin_id}")
            return True

        except Exception as e:
            self.logger.warning(f"插件停止失败2 {plugin_id}, {e}")
            return False

    async def invoke_plugin_stream(
        self,
        session: AsyncSession,
        plugin_id: str,
        invoke_request: dict[str, Any],
        timeout: int = 60,
    ):
        """流式调用插件方法（懒加载模式）"""
        # 确保插件准备就绪（懒加载：从OSS下载 + 启动）
        await self._ensure_plugin_ready(session, plugin_id)

        # 更新最后访问时间(暂时不更新访问时间，会影响性能，应该改为异步的方式)
        # await self._update_plugin_last_accessed(plugin_id)

        # 记录调用开始时间
        invoke_start_time = time.time()
        success = False
        chunk_count = 0

        action = invoke_request.get("action", "unknown")

        try:
            # 调用插件流式方法
            runtime = self.running_plugins[plugin_id]

            self.logger.info(f"开始流式调用插件: {plugin_id}.{action}")

            # 用于保存最后3条数据的滑动窗口
            last_chunks = []

            result = runtime.invoke_stream(invoke_request, timeout)
            if isinstance(result, AsyncGenerator):
                async for chunk in result:
                    chunk_count += 1

                    # 前5条直接打印
                    if chunk_count <= 5:
                        self.logger.info(
                            f"收到[{plugin_id}]数据块 #{chunk_count}: {str(chunk)[:1000]}..."
                        )

                    # 维护最后3条数据的滑动窗口
                    last_chunks.append((chunk_count, str(chunk)[:1000]))
                    if len(last_chunks) > 3:
                        last_chunks.pop(0)

                    yield chunk

            success = True

        except PluginError as e:
            # 插件错误，可能是插件进程已退出
            self.logger.error(f"插件错误: {e}")
            # 停止插件
            await self.stop_plugin(plugin_id, session)
            raise e
        except Exception as e:
            raise e

        finally:
            # 打印最后3条数据（仅当总数大于5时，避免重复）
            if chunk_count > 5 and "last_chunks" in locals() and last_chunks:
                self.logger.info("--- 最后3条流式数据块 ---")
                for chunk_num, chunk_content in last_chunks:
                    self.logger.info(
                        f"收到[{plugin_id}]数据块 #{chunk_num}: {chunk_content}..."
                    )

            # 记录调用时间
            try:
                invoke_time = time.time() - invoke_start_time
                self.performance_monitor.record_invoke_time(
                    plugin_id, invoke_time, success
                )

                # 记录资源使用情况

                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                self.performance_monitor.record_resource_usage(
                    plugin_id, memory_mb, cpu_percent
                )
            except:
                pass  # 忽略资源监控错误

            self.logger.info(
                f"流式插件调用完成: {plugin_id}.{action} (用时: {invoke_time:.3f}秒, 成功: {success}, 数据块数: {chunk_count})",
            )

    async def _update_plugin_status(
        self, session: AsyncSession, plugin_id: str, status: PluginStatus
    ):
        """更新插件状态（通过 Provider 更新 Tenant 侧 + AI 侧运行时状态）"""
        # 更新内存状态
        if plugin_id in self.plugins:
            self.plugins[plugin_id].status = status

        try:
            # 1. 通过 Provider 更新 Tenant 侧状态
            provider = get_plugin_installation_provider()
            status_str = "ACTIVE" if status == PluginStatus.ACTIVE else "INACTIVE"
            await provider.update_installation(
                self.tenant_id, plugin_id, {"status": status_str}
            )
            self.logger.debug(
                f"已通过 Provider 更新插件状态: {plugin_id} -> {status_str}"
            )

            # 2. 更新 AI 侧的 plugin_runtime_states 表
            result = await session.execute(
                select(PluginRuntimeState).where(
                    and_(
                        PluginRuntimeState.tenant_id == self.tenant_id,
                        PluginRuntimeState.plugin_id == plugin_id,
                    ),
                ),
            )
            runtime_state = result.scalar_one_or_none()

            if runtime_state:
                runtime_state.status = (
                    "active" if status == PluginStatus.ACTIVE else "inactive"
                )
                if status == PluginStatus.ACTIVE:
                    runtime_state.last_started_at = datetime.now()
                elif status == PluginStatus.INACTIVE:
                    runtime_state.last_stopped_at = datetime.now()
                await session.flush()
                self.logger.debug(f"已更新插件运行时状态: {plugin_id}")
        except Exception:
            self.logger.exception(f"更新插件状态失败: {plugin_id}")
            # 不抛出异常，因为这不是关键功能

    async def _parse_plugin_package(self, plugin_package: bytes) -> PluginPackageInfo:
        """解析插件包，提取配置和_assets内容"""
        try:
            # 计算插件包哈希值
            package_hash = hashlib.sha256(plugin_package).hexdigest()

            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # 保存插件包到临时文件
                package_file = temp_path / "plugin.zip"
                with open(package_file, "wb") as f:
                    f.write(plugin_package)

                # 解压插件包
                extract_dir = temp_path / "extracted"
                extract_dir.mkdir()
                with zipfile.ZipFile(package_file, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)

                # 构建配置文件路径 - 查找插件目录下的manifest.yaml
                config_path = extract_dir / "manifest.yaml"

                if config_path.exists() is False:
                    self.logger.warning(f"插件配置文件不存在: {config_path}")
                    raise ValueError("插件包中未找到有效的manifest文件")

                # 创建PluginConfig对象
                plugin_config, assets = await self._load_plugin_config(config_path)

                # 创建并返回插件包信息
                return PluginPackageInfo(
                    config=plugin_config, assets=assets, package_hash=package_hash
                )

        except Exception as e:
            raise e

    async def _find_and_parse_manifest(self, extract_dir: Path) -> dict | None:
        """查找并解析manifest文件"""
        # 查找manifest.yaml或manifest.json
        manifest_files = [extract_dir / "manifest.yaml", extract_dir / "manifest.json"]

        # 递归查找
        for pattern in ["**/manifest.yaml", "**/manifest.json"]:
            manifest_files.extend(extract_dir.glob(pattern))

        for manifest_file in manifest_files:
            if manifest_file.exists():
                try:
                    with open(manifest_file, encoding="utf-8") as f:
                        if manifest_file.suffix == ".yaml":
                            return yaml.safe_load(f)
                        else:
                            return json.load(f)
                except Exception as e:
                    self.logger.warning(f"解析manifest文件失败 {manifest_file}: {e}")
                    continue

        return None

    async def _collect_plugin_assets(self, extract_dir: Path) -> list[PluginAssetFile]:
        """收集插件_assets目录中的所有文件"""
        assets = []

        # 查找_assets目录
        assets_dir = None

        # 首先在根目录查找
        root_assets_dir = extract_dir / "_assets"
        if root_assets_dir.exists() and root_assets_dir.is_dir():
            assets_dir = root_assets_dir
        else:
            # 递归查找_assets目录
            for path in extract_dir.rglob("_assets"):
                if path.is_dir():
                    assets_dir = path
                    break

        if not assets_dir:
            self.logger.info("插件包中未找到_assets目录")
            return assets

        self.logger.info(f"找到_assets目录: {assets_dir}")

        # 递归扫描_assets目录中的所有文件
        try:
            for file_path in assets_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        asset_file = PluginAssetFile.from_file_path(
                            file_path, assets_dir
                        )
                        assets.append(asset_file)
                        self.logger.debug(
                            f"收集资源文件: {asset_file.relative_path} ({asset_file.file_size} bytes)"
                        )
                    except Exception as e:
                        self.logger.warning(f"跳过无法读取的文件 {file_path}: {e}")

        except Exception as e:
            self.logger.warning(f"扫描_assets目录失败 {assets_dir}: {e}")

        self.logger.info(f"共收集到 {len(assets)} 个资源文件")
        return assets

    async def _validate_plugin(self, plugin_config: PluginConfig):
        """验证插件"""
        # 基本验证
        if not plugin_config.configuration.name:
            raise ValueError("插件名称不能为空")

        if not plugin_config.configuration.version:
            raise ValueError("插件版本不能为空")

        if not plugin_config.configuration.author:
            raise ValueError("插件作者不能为空")

        if not plugin_config.configuration.type:
            raise ValueError("插件类型不能为空")

        # 检查插件类型（目前仅支持工具或者模型类型的插件）
        if (
            len(plugin_config.tools_configuration or []) == 0
            and len(plugin_config.models_configuration or []) == 0
        ):
            raise ValueError("目前仅支持工具或者模型类型的插件，请检查插件包")

    async def _install_plugin_files(self, plugin_id: str, plugin_package: bytes):
        """安装插件文件"""
        # 创建插件目录
        plugin_dir = self.workspace_dir / plugin_id
        plugin_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 保存原始插件包
            package_path = plugin_dir / "plugin.zip"
            with open(package_path, "wb") as f:
                f.write(plugin_package)

            # 解压插件包
            with zipfile.ZipFile(package_path, "r") as zip_ref:
                zip_ref.extractall(plugin_dir)

            self.logger.info(f"插件文件准备完成: {plugin_dir}")

        except Exception as e:
            # 清理失败的安装
            if plugin_dir.exists():
                import shutil

                shutil.rmtree(plugin_dir, ignore_errors=True)
            raise ValueError(f"插件文件准备失败: {e}")

    async def _register_plugin_installation(
        self,
        session: AsyncSession,
        plugin_config: PluginConfig,
        plugin_id: str,
        install_info: dict[str, Any],
        auto_start: bool,
        config_override: dict[str, Any],
    ):
        """注册插件安装到数据库和内存"""
        try:
            # 创建PluginInfo对象
            plugin_info = PluginInfo(config=plugin_config, installed_at=datetime.now())

            # 注册插件到内存
            self.plugins[plugin_id] = plugin_info

            # 保存插件信息到数据库
            await self._save_plugin_installation_to_database(
                session,
                plugin_config,
                plugin_id,
                install_info,
                auto_start,
                config_override,
            )

            self.logger.info(f"插件注册成功: {plugin_id}")

        except Exception:
            # 清理失败的注册
            if plugin_id in self.plugins:
                del self.plugins[plugin_id]
            raise

    async def _save_plugin_installation_to_database(
        self,
        session: AsyncSession,
        plugin_config: PluginConfig,
        plugin_id: str,
        install_info: dict[str, Any],
        auto_start: bool,
        config_override: dict[str, Any],
    ):
        """保存插件安装信息到数据库"""
        provider = get_plugin_installation_provider()

        plugin_unique_identifier = f"{plugin_id}@{plugin_config.configuration.version}"
        installation_dto = PluginInstallationDTO(
            tenant_id=self.tenant_id,
            plugin_id=plugin_id,
            plugin_unique_identifier=plugin_unique_identifier,
            status="PENDING",
            auto_start=auto_start,
            plugin_type=self.convert_to_plugin_type(plugin_config).value,
            runtime_type="local",
        )

        try:
            # 1. 创建 Tenant 侧记录
            await provider.create_installation(self.tenant_id, installation_dto)

            # 2. 创建 AI 侧 PluginConfig
            ai_config = AIPluginConfig(
                tenant_id=self.tenant_id,
                plugin_id=plugin_id,
                plugin_unique_identifier=plugin_unique_identifier,
                plugin_config=plugin_config.model_dump(mode="json")
                if hasattr(plugin_config, "model_dump")
                else plugin_config.__dict__,
                runtime_config={},
            )
            session.add(ai_config)

            # 3. 创建 AI 侧 PluginRuntimeState
            runtime_state = PluginRuntimeState(
                tenant_id=self.tenant_id,
                plugin_id=plugin_id,
                status="active",
            )
            session.add(runtime_state)

            await session.flush()

            # 4. 更新状态为 ACTIVE
            await provider.update_installation(
                self.tenant_id,
                plugin_id,
                {"status": "ACTIVE"},
            )

            self.logger.info(f"插件安装数据保存成功: {plugin_id}")

        except Exception as e:
            # 标记安装失败
            try:
                await provider.update_installation(
                    self.tenant_id,
                    plugin_id,
                    {"status": "FAILED", "error": str(e)},
                )
            except Exception:
                self.logger.exception(f"更新安装状态失败: {plugin_id}")
            raise

    def convert_to_plugin_type(self, plugin_config: PluginConfig) -> DBPluginType:
        """将插件配置转换为数据库插件类型"""
        if len(plugin_config.models_configuration or []) > 0:
            return DBPluginType.MODEL
        if len(plugin_config.tools_configuration or []) > 0:
            return DBPluginType.TOOL
        if len(plugin_config.agent_strategies_configuration or []) > 0:
            return DBPluginType.AGENT
        else:
            raise ValueError("插件类型不正确")

    async def get_plugin_performance_metrics(self, plugin_id: str) -> dict[str, Any]:
        """获取单个插件的性能指标"""
        return self.performance_monitor.get_plugin_metrics(plugin_id)

    async def get_all_plugins_performance_metrics(self) -> dict[str, dict[str, Any]]:
        """获取所有插件的性能指标"""
        metrics = {}
        for plugin_id in self.plugins:
            metrics[plugin_id] = self.performance_monitor.get_plugin_metrics(plugin_id)
        return metrics

    async def get_system_performance_overview(self) -> dict[str, Any]:
        """获取系统性能总览"""
        return self.performance_monitor.get_system_overview()

    async def get_performance_report(self) -> dict[str, Any]:
        """获取完整的性能报告"""
        return {
            "system_overview": await self.get_system_performance_overview(),
            "plugin_metrics": await self.get_all_plugins_performance_metrics(),
            "generated_at": datetime.now(),
        }

    async def get_warmup_status(self) -> WarmupStatusInfo:
        """获取预热状态"""
        return await self.warmup_manager.get_warmup_status()

    async def configure_warmup(self, config: WarmupConfig) -> bool:
        """配置预热参数"""
        return await self.warmup_manager.configure_warmup(config)

    async def manual_warmup(
        self, session: AsyncSession, plugin_ids: list[str] | None = None
    ) -> WarmupExecutionResult:
        """手动预热插件"""
        if plugin_ids:
            # 预热指定插件
            warmed_plugins = []
            failed_plugins = []

            for plugin_id in plugin_ids:
                result = await self.warmup_manager.warmup_plugin(session, plugin_id)
                if result.result == PluginWarmupResult.SUCCESS:
                    warmed_plugins.append(plugin_id)
                else:
                    failed_plugins.append(plugin_id)

            return WarmupExecutionResult(
                status=WarmupStatus.COMPLETED,
                warmed_plugins=warmed_plugins,
                failed_plugins=failed_plugins,
                warmup_time=datetime.now(),
            )
        else:
            # 自动预热
            return await self.warmup_manager.auto_warmup(session)

    async def analyze_warmup_candidates(self) -> list[PluginCandidate]:
        """分析预热候选插件"""
        return await self.warmup_manager.analyze_warmup_candidates()

    # ===== 插件资源文件管理方法 =====

    async def get_plugin_asset(self, plugin_id: str, asset_path: str) -> bytes | None:
        """获取插件资源文件内容"""
        try:
            # 检查插件是否存在
            if plugin_id not in self.plugins:
                self.logger.warning(f"插件不存在: {plugin_id}")
                return None

            plugin_info = self.plugins[plugin_id]

            plugin_config = plugin_info.config
            if not plugin_config:
                self.logger.warning(f"插件配置不存在: {plugin_id}")
                return None

            version = plugin_config.configuration.version

            # 先尝试从本地读取
            local_asset_path = self.workspace_dir / plugin_id / "_assets" / asset_path

            # 检查路径是否安全，是否存在..等
            if ".." in asset_path:
                self.logger.warning(f"资源文件路径不安全: {asset_path}")
                return None

            if local_asset_path.exists():
                try:
                    with open(local_asset_path, "rb") as f:
                        content = f.read()
                    self.logger.debug(f"从本地读取资源文件: {local_asset_path}")
                    return content
                except Exception as e:
                    self.logger.warning(
                        f"读取本地资源文件失败: {local_asset_path}, {e}"
                    )

            # 如果本地不存在，尝试从OSS下载
            self.logger.info(
                f"本地资源文件不存在，尝试从OSS下载: {plugin_id}/{asset_path}"
            )
            return await self._download_plugin_asset_from_oss(
                plugin_id, version, asset_path
            )

        except Exception:
            self.logger.exception(f"获取插件资源文件失败: {plugin_id}/{asset_path}")
            return None

    async def shutdown(self):
        """关闭插件管理器"""
        self.logger.info(f"关闭租户插件管理器: {self.tenant_id}")

        # 停止所有运行中的插件
        for plugin_id in list(self.running_plugins.keys()):
            await self.stop_plugin(plugin_id)

        # 清理资源
        self.plugins.clear()
        self.running_plugins.clear()

        self.logger.info(f"租户插件管理器已关闭: {self.tenant_id}")


class PluginManagerFactory:
    """多租户插件管理器工厂类"""

    _instances: dict[str, TenantPluginManager] = {}
    _lock = asyncio.Lock()

    # ==================== 多进程安全机制 ====================
    _initialization_pid = os.getpid()
    """初始化进程的PID（父进程）"""

    _process_instances: dict[int, dict[str, TenantPluginManager]] = {}
    """子进程级别的插件管理器缓存"""

    @classmethod
    async def get_manager(
        cls, tenant_id: str, session: AsyncSession
    ) -> TenantPluginManager:
        """获取指定租户的插件管理器实例（多进程安全）"""
        current_pid = os.getpid()

        async with cls._lock:
            # 检查是否是子进程（不是初始化进程）
            if current_pid != cls._initialization_pid:
                # 这是子进程，需要创建新的插件管理器实例
                if current_pid not in cls._process_instances:
                    cls._process_instances[current_pid] = {}
                    logger.info(f"检测到子进程 {current_pid}，初始化新的插件管理器缓存")

                if tenant_id not in cls._process_instances[current_pid]:
                    logger.info(
                        f"子进程 {current_pid} 创建新的插件管理器实例: tenant_id={tenant_id}"
                    )

                    # 为子进程创建新的插件管理器实例
                    manager = TenantPluginManager(tenant_id)
                    await manager.initialize(session)

                    # 清理继承的插件运行时状态，因为父进程的插件进程在子进程中不可用
                    manager.running_plugins.clear()
                    logger.info(f"子进程 {current_pid} 已清理继承的插件运行时状态")

                    cls._process_instances[current_pid][tenant_id] = manager

                return cls._process_instances[current_pid][tenant_id]
            else:
                # 这是主进程，使用全局实例
                if tenant_id not in cls._instances:
                    manager = TenantPluginManager(tenant_id)
                    await manager.initialize(session)
                    cls._instances[tenant_id] = manager
                return cls._instances[tenant_id]

    @classmethod
    async def get_all_managers(cls) -> dict[str, TenantPluginManager]:
        """获取所有租户的插件管理器"""
        return cls._instances.copy()

    @classmethod
    async def shutdown_all(cls):
        """关闭所有租户的插件管理器"""

        try:
            async with cls._lock:
                for manager in cls._instances.values():
                    await manager.shutdown()
                cls._instances.clear()
        except Exception as e:
            logger.warning(f"关闭所有租户的插件管理器失败: {e}")

        try:
            import platform
            import subprocess

            name = settings.plugin.plugin_base_dir.name
            logger.info(f"plugin_base_dir: {name}")

            # 根据操作系统选择不同的进程清理命令
            if platform.system() == "Windows":
                # Windows系统使用taskkill命令
                # 组装Windows进程清理参数
                windows_kill_args = [
                    "taskkill",
                    "/f",  # 强制终止
                    "/im",
                    "python.exe",  # 进程映像名称
                    "/fi",
                    f"WINDOWTITLE eq *{name}*",  # 窗口标题过滤
                ]
                result = subprocess.run(
                    windows_kill_args, capture_output=True, text=True
                )
            else:
                # Unix/Linux系统使用pkill命令
                # 组装Unix/Linux进程清理参数
                unix_kill_args = [
                    "pkill",
                    "-f",  # 使用完整命令行匹配
                    f"{name}.*python",  # 进程名模式匹配
                ]
                result = subprocess.run(unix_kill_args, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("强制清理插件进程完成")

        except Exception as kill_error:
            logger.warning(f"强制清理失败: {kill_error}")
