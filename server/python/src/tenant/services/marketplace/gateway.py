"""插件市场网关服务"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.models import TenantPluginDefinition, TenantPluginMarketplace
from tenant.services.marketplace.adapters.dify_adapter import DifyAdapter
from tenant.services.marketplace.adapters.modelscope_adapter import ModelScopeAdapter
from tenant.services.marketplace.adapters.agentskills_adapter import AgentSkillsAdapter
from tenant.services.marketplace.adapters.local_skill_adapter import LocalSkillAdapter
from tenant.services.marketplace.adapters.modelscope_skill_adapter import (
    ModelScopeSkillAdapter,
)
from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class MarketplaceGateway:
    """插件市场网关服务"""

    _adapters: dict[str, type] = {
        "dify": DifyAdapter,
        "modelscope": ModelScopeAdapter,
        "agentskills": AgentSkillsAdapter,
        "modelscope-skill": ModelScopeSkillAdapter,
        "local-skill": LocalSkillAdapter,
    }

    def _get_adapter(self, market_type: str) -> MarketplaceAdapter:
        """获取适配器实例"""
        adapter_class = self._adapters.get(market_type)
        if not adapter_class:
            raise ValueError(f"不支持的市场类型: {market_type}")
        return adapter_class()

    def _build_adapter_config(self, marketplace: TenantPluginMarketplace) -> dict:
        """构建适配器配置"""
        return {
            "url": marketplace.url,
            "auth_type": marketplace.auth_type,
            "auth_config": marketplace.auth_config,
        }

    # ==================== 市场配置管理 ====================

    async def create_marketplace(
        self,
        session: AsyncSession,
        name: str,
        code: str,
        type: str,
        url: str,
        auth_type: str = "none",
        auth_config: dict | None = None,
        description: str | None = None,
    ) -> TenantPluginMarketplace:
        """创建市场配置"""
        # 检查 code 是否已存在
        existing = await session.execute(
            select(TenantPluginMarketplace).where(TenantPluginMarketplace.code == code)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"市场编码已存在: {code}")

        marketplace = TenantPluginMarketplace(
            name=name,
            code=code,
            type=type,
            url=url,
            auth_type=auth_type,
            auth_config=auth_config or {},
            description=description,
        )
        session.add(marketplace)
        await session.flush()
        return marketplace

    async def get_marketplace(
        self,
        session: AsyncSession,
        marketplace_id: str,
    ) -> TenantPluginMarketplace | None:
        """获取市场配置"""
        result = await session.execute(
            select(TenantPluginMarketplace).where(TenantPluginMarketplace.id == marketplace_id)
        )
        return result.scalar_one_or_none()

    async def list_marketplaces(
        self,
        session: AsyncSession,
        is_enabled: bool | None = None,
        type: str | None = None,
    ) -> Sequence[TenantPluginMarketplace]:
        """获取市场列表"""
        query = select(TenantPluginMarketplace)
        if is_enabled is not None:
            query = query.where(TenantPluginMarketplace.is_enabled == is_enabled)
        if type is not None:
            query = query.where(TenantPluginMarketplace.type == type)
        query = query.order_by(TenantPluginMarketplace.created_at.desc())
        result = await session.execute(query)
        return result.scalars().all()

    async def update_marketplace(
        self,
        session: AsyncSession,
        marketplace_id: str,
        **kwargs: Any,
    ) -> TenantPluginMarketplace:
        """更新市场配置"""
        marketplace = await self.get_marketplace(session, marketplace_id)
        if not marketplace:
            raise ValueError(f"市场不存在: {marketplace_id}")

        for key, value in kwargs.items():
            if hasattr(marketplace, key):
                setattr(marketplace, key, value)

        await session.flush()
        return marketplace

    async def delete_marketplace(
        self,
        session: AsyncSession,
        marketplace_id: str,
    ) -> None:
        """删除市场配置"""
        marketplace = await self.get_marketplace(session, marketplace_id)
        if not marketplace:
            raise ValueError(f"市场不存在: {marketplace_id}")

        await session.delete(marketplace)

    # ==================== 连接测试 ====================

    async def test_connection(
        self,
        session: AsyncSession,
        marketplace_id: str,
    ) -> MarketplaceTestResult:
        """测试市场连接"""
        marketplace = await self.get_marketplace(session, marketplace_id)
        if not marketplace:
            raise ValueError(f"市场不存在: {marketplace_id}")

        adapter = self._get_adapter(marketplace.type)
        config = self._build_adapter_config(marketplace)
        return await adapter.test_connection(config)

    # ==================== 远程插件浏览 ====================

    async def list_remote_plugins(
        self,
        session: AsyncSession,
        marketplace_id: str,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """浏览远程插件列表"""
        marketplace = await self.get_marketplace(session, marketplace_id)
        if not marketplace:
            raise ValueError(f"市场不存在: {marketplace_id}")

        if not marketplace.is_enabled:
            raise ValueError(f"市场已禁用: {marketplace.name}")

        adapter = self._get_adapter(marketplace.type)
        config = self._build_adapter_config(marketplace)
        return await adapter.list_plugins(config, keyword, plugin_type, page, page_size)

    async def get_remote_plugin(
        self,
        session: AsyncSession,
        marketplace_id: str,
        plugin_id: str,
    ) -> RemotePluginInfo | None:
        """获取远程插件详情"""
        marketplace = await self.get_marketplace(session, marketplace_id)
        if not marketplace:
            raise ValueError(f"市场不存在: {marketplace_id}")

        adapter = self._get_adapter(marketplace.type)
        config = self._build_adapter_config(marketplace)
        return await adapter.get_plugin(config, plugin_id)

    # ==================== 插件同步 ====================

    async def sync_plugins(
        self,
        session: AsyncSession,
        marketplace_id: str,
        plugins: list[dict[str, str]],
    ) -> dict[str, Any]:
        """同步选中插件"""
        from tenant.services.plugin_package_service import plugin_package_service
        from tenant.services.plugin_storage_service import plugin_storage_service

        marketplace = await self.get_marketplace(session, marketplace_id)
        if not marketplace:
            raise ValueError(f"市场不存在: {marketplace_id}")
        if not marketplace.is_enabled:
            raise ValueError(f"市场已禁用: {marketplace.name}")

        adapter = self._get_adapter(marketplace.type)
        config = self._build_adapter_config(marketplace)

        success = []
        failed = []
        skipped = []

        for plugin_item in plugins:
            plugin_id = plugin_item["plugin_id"]
            plugin_type = plugin_item.get("plugin_type", "tool")

            try:
                # 1. 获取远程插件信息
                remote_info = await adapter.get_plugin(config, plugin_id)
                if not remote_info:
                    failed.append({"plugin_id": plugin_id, "message": "远程插件不存在"})
                    continue

                # 2. 检查本地是否已存在（取最新的启用版本）
                existing = await session.execute(
                    select(TenantPluginDefinition)
                    .where(
                        TenantPluginDefinition.plugin_id == plugin_id,
                        TenantPluginDefinition.is_enabled == True,
                    )
                    .order_by(TenantPluginDefinition.created_at.desc())
                    .limit(1)
                )
                existing_def = existing.scalar_one_or_none()

                if existing_def and existing_def.remote_version == remote_info.version:
                    skipped.append({"plugin_id": plugin_id, "reason": "相同版本已存在"})
                    continue

                # 3. 下载插件包
                package_data, checksum = await adapter.download_plugin(config, plugin_id)

                # 4. 解析验证
                package_info = plugin_package_service.parse_package_from_bytes(package_data)

                # 5. 存储到 MinIO
                storage_path = await plugin_storage_service.upload_plugin_package(
                    plugin_id=plugin_id,
                    version=remote_info.version,
                    package_data=package_data,
                )

                # 6. 创建/更新 plugin_definitions 记录
                if existing_def:
                    existing_def.declaration = package_info.declaration
                    existing_def.remote_version = remote_info.version
                    existing_def.local_version = remote_info.version
                    existing_def.update_available = False
                    existing_def.source_type = "remote"
                    existing_def.marketplace_id = marketplace_id
                else:
                    new_def = TenantPluginDefinition(
                        plugin_id=plugin_id,
                        plugin_unique_identifier=f"{plugin_id}:{remote_info.version}@{checksum}",
                        declaration=package_info.declaration,
                        refers=0,
                        install_type="remote",
                        manifest_type=plugin_type,
                        marketplace_id=marketplace_id,
                        remote_plugin_id=plugin_id,
                        remote_version=remote_info.version,
                        local_version=remote_info.version,
                        source_type="remote",
                    )
                    session.add(new_def)

                success.append({"plugin_id": plugin_id, "version": remote_info.version})

            except Exception as e:
                logger.error(f"同步插件失败: {plugin_id}, 错误: {e}")
                failed.append({"plugin_id": plugin_id, "message": str(e)})

        # 更新最后同步时间
        marketplace.last_sync_at = datetime.utcnow()
        marketplace.last_sync_status = "success" if not failed else "partial"

        return {"success": success, "failed": failed, "skipped": skipped}

    async def check_updates(
        self,
        session: AsyncSession,
        marketplace_id: str,
    ) -> Sequence[PluginUpdateInfo]:
        """检查插件更新"""
        marketplace = await self.get_marketplace(session, marketplace_id)
        if not marketplace:
            raise ValueError(f"市场不存在: {marketplace_id}")

        adapter = self._get_adapter(marketplace.type)
        config = self._build_adapter_config(marketplace)

        # 查询该市场来源的插件定义
        result = await session.execute(
            select(TenantPluginDefinition).where(
                TenantPluginDefinition.source_type == "remote",
                TenantPluginDefinition.marketplace_id == marketplace_id,
            )
        )
        local_plugins = result.scalars().all()

        # 批量检查更新
        plugins_to_check = [
            {"plugin_id": p.plugin_id, "current_version": p.local_version}
            for p in local_plugins
        ]

        return await adapter.check_updates(config, plugins_to_check)

    async def apply_update(
        self,
        session: AsyncSession,
        marketplace_id: str,
        plugin_id: str,
    ) -> dict[str, Any]:
        """应用插件更新"""
        marketplace = await self.get_marketplace(session, marketplace_id)
        if not marketplace:
            raise ValueError(f"市场不存在: {marketplace_id}")

        # 获取本地插件定义（取最新的启用版本）
        result = await session.execute(
            select(TenantPluginDefinition)
            .where(
                TenantPluginDefinition.plugin_id == plugin_id,
                TenantPluginDefinition.source_type == "remote",
                TenantPluginDefinition.is_enabled == True,
            )
            .order_by(TenantPluginDefinition.created_at.desc())
            .limit(1)
        )
        local_def = result.scalar_one_or_none()
        if not local_def:
            raise ValueError(f"插件不存在: {plugin_id}")

        old_version = local_def.local_version

        # 重新同步该插件
        sync_result = await self.sync_plugins(
            session, marketplace_id, [{"plugin_id": plugin_id}]
        )

        return {
            "plugin_id": plugin_id,
            "old_version": old_version,
            "new_version": local_def.local_version or old_version,
            "status": "updated" if sync_result["success"] else "failed",
        }

    async def sync_skill_from_marketplace(
        self,
        session: AsyncSession,
        marketplace_id: str,
        skill_id: str,
    ) -> TenantPluginDefinition:
        """从市场同步单个 Skill 到本地

        Args:
            session: 数据库会话
            marketplace_id: 市场 ID
            skill_id: Skill ID（格式：author/name）

        Returns:
            TenantPluginDefinition: 创建或更新的插件定义

        Raises:
            ValueError: 市场不存在或 Skill 不存在
        """
        from tenant.services.plugin_storage_service import plugin_storage_service

        marketplace = await self.get_marketplace(session, marketplace_id)
        if not marketplace:
            raise ValueError(f"市场不存在: {marketplace_id}")
        if not marketplace.is_enabled:
            raise ValueError(f"市场已禁用: {marketplace.name}")

        adapter = self._get_adapter(marketplace.type)
        config = self._build_adapter_config(marketplace)

        # 1. 获取 Skill 元数据
        skill_info = await adapter.get_plugin(config, skill_id)
        if not skill_info:
            raise ValueError(f"Skill 不存在: {skill_id}")

        # 2. 下载 Skill 包
        skill_data, checksum = await adapter.download_plugin(
            config, skill_id, version=skill_info.version
        )

        # 3. 上传到 MinIO
        storage_key = await plugin_storage_service.upload_skill_package(
            skill_id=skill_id,
            skill_data=skill_data,
            checksum=checksum,
            version=skill_info.version,
        )

        # 4. 构建 declaration
        skill_runtime = "none" if skill_info.skill_type == "knowledge" else "sandbox"
        declaration = {
            "skill": {
                "skill_type": skill_info.skill_type or "knowledge",
                "runtime": skill_runtime,
            },
            "metadata": {
                "name": skill_info.name,
                "description": skill_info.description,
                "version": skill_info.version,
                "author": skill_info.author,
                "tags": skill_info.tags,
            },
        }

        # 5. 检查是否已存在
        existing = await session.execute(
            select(TenantPluginDefinition).where(
                TenantPluginDefinition.plugin_id == skill_id,
                TenantPluginDefinition.is_enabled == True,  # noqa: E712
            )
        )
        existing_def = existing.scalar_one_or_none()

        if existing_def:
            # 更新现有记录
            existing_def.declaration = declaration
            existing_def.skill_type = skill_info.skill_type
            existing_def.runtime_type = skill_runtime
            existing_def.remote_version = skill_info.version
            existing_def.local_version = skill_info.version
            existing_def.update_available = False
            existing_def.source_type = "remote"
            existing_def.marketplace_id = marketplace_id
            await session.flush()
            return existing_def

        # 6. 创建新记录
        new_def = TenantPluginDefinition(
            plugin_id=skill_id,
            plugin_unique_identifier=f"{skill_id}:{skill_info.version}@{checksum}",
            declaration=declaration,
            refers=0,
            install_type="remote",
            manifest_type="skill",
            skill_type=skill_info.skill_type,
            runtime_type=skill_runtime,
            marketplace_id=marketplace_id,
            remote_plugin_id=skill_id,
            remote_version=skill_info.version,
            local_version=skill_info.version,
            source_type="remote",
        )
        session.add(new_def)
        await session.flush()
        return new_def


# 单例实例
marketplace_gateway = MarketplaceGateway()
