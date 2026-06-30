"""插件市场网关服务"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.models import TenantPluginMarketplace
from tenant.services.marketplace.adapters.dify_adapter import DifyAdapter
from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    RemotePluginInfo,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class MarketplaceGateway:
    """插件市场网关服务"""

    _adapters: dict[str, type] = {
        "dify": DifyAdapter,
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
    ) -> Sequence[TenantPluginMarketplace]:
        """获取市场列表"""
        query = select(TenantPluginMarketplace)
        if is_enabled is not None:
            query = query.where(TenantPluginMarketplace.is_enabled == is_enabled)
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


# 单例实例
marketplace_gateway = MarketplaceGateway()
