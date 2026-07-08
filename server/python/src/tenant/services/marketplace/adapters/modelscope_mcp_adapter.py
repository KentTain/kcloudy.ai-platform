"""ModelScope MCP 市场适配器

魔搭社区提供独立的 MCP server 市场，与模型市场、Skill 市场并列。
本适配器符合 ModelScope OpenAPI 规范（https://modelscope.cn/docs/openapi）。

关键特性：
- MCP 列表使用 PUT 方法，请求体传参
- MCP 连接信息通过 get_operational_url=true 参数获取
- MCP 服务是远程服务，无安装包，返回连接配置清单
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

import httpx
from loguru import logger

from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class ModelScopeMcpAdapter(MarketplaceAdapter):
    """ModelScope MCP 市场适配器（符合官方 OpenAPI 规范）"""

    API_BASE = "https://modelscope.cn/openapi/v1"

    @property
    def market_type(self) -> str:
        """市场类型标识"""
        return "modelscope-mcp"

    def _build_headers(self, config: dict) -> dict[str, str]:
        """构建请求头"""
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        auth_config = config.get("auth_config", {})
        api_token = auth_config.get("api_token", "")
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        return headers

    def _get_base_url(self, config: dict) -> str:
        """获取 API 基础 URL"""
        return config.get("url", self.API_BASE)

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接"""
        headers = self._build_headers(config)
        base_url = self._get_base_url(config)
        start_time = time.time()

        try:
            # 使用 PUT 方法，请求体传参
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{base_url}/mcp/servers",
                    headers=headers,
                    json={"page_number": 1, "page_size": 1},
                )
                latency_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    total = data.get("data", {}).get("total_count", 0)
                    return MarketplaceTestResult(
                        success=True,
                        message="连接成功",
                        plugin_count=total,
                        latency_ms=latency_ms,
                    )

                return MarketplaceTestResult(
                    success=False,
                    message=f"连接失败: HTTP {response.status_code}",
                    latency_ms=latency_ms,
                )

        except httpx.TimeoutException:
            return MarketplaceTestResult(success=False, message="连接超时")
        except Exception as e:
            logger.error(f"测试 ModelScope MCP 市场连接失败: {e}")
            return MarketplaceTestResult(success=False, message=f"连接异常: {str(e)}")

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取远程 MCP server 列表"""
        headers = self._build_headers(config)
        base_url = self._get_base_url(config)

        # PUT 请求体传参
        body: dict[str, Any] = {"page_number": page, "page_size": page_size}
        if keyword:
            body["search"] = keyword

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{base_url}/mcp/servers",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            data = response.json()

        # 解析响应：data.mcp_server_list
        servers_data = data.get("data", {}).get("mcp_server_list", [])
        total = data.get("data", {}).get("total_count", 0)
        plugins = [self._parse_mcp(item) for item in servers_data]

        return plugins, total

    async def get_plugin(self, config: dict, plugin_id: str) -> RemotePluginInfo | None:
        """获取单个 MCP server 详情（含连接信息）"""
        headers = self._build_headers(config)
        base_url = self._get_base_url(config)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 必须传 get_operational_url=true 才能获取连接信息
                response = await client.get(
                    f"{base_url}/mcp/servers/{plugin_id}",
                    headers=headers,
                    params={"get_operational_url": "true"},
                )

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                data = response.json()
                return self._parse_mcp_detail(data.get("data", {}))

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """生成 MCP server 配置清单

        MCP server 是远程服务，没有可下载的安装包。这里返回描述该 server
        连接信息的 JSON 清单，供 plugin_definitions 存储为声明。
        """
        remote_info = await self.get_plugin(config, plugin_id)
        if not remote_info:
            raise ValueError(f"MCP server {plugin_id} not found")

        # 从 skill_metadata 获取连接信息
        metadata = remote_info.skill_metadata or {}
        transport = metadata.get("transport_type", "streamable_http")
        auth_required = metadata.get("auth_required", False)

        manifest = {
            "mcp": {
                "server_url": remote_info.download_url,
                "transport": transport,
                "auth_required": auth_required,
            },
            "metadata": {
                "name": remote_info.name,
                "description": remote_info.description,
                "version": remote_info.version,
                "author": remote_info.author,
                "tags": remote_info.tags,
            },
        }
        data = json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(data).hexdigest()
        return data, checksum

    async def check_updates(
        self,
        config: dict,
        plugins: Sequence[dict],
    ) -> Sequence[PluginUpdateInfo]:
        """检查 MCP server 更新"""
        results: list[PluginUpdateInfo] = []

        for plugin in plugins:
            plugin_id = plugin.get("plugin_id")
            current_version = plugin.get("current_version")

            if not plugin_id:
                continue

            try:
                remote = await self.get_plugin(config, plugin_id)
                if remote:
                    has_update = remote.version != current_version
                    results.append(PluginUpdateInfo(
                        plugin_id=plugin_id,
                        current_version=current_version or "",
                        latest_version=remote.version,
                        has_update=has_update,
                        changelog=None,
                    ))
            except Exception as e:
                logger.warning(f"检查 MCP server 更新失败: {plugin_id}, 错误: {e}")

        return results

    def _parse_mcp(self, item: dict) -> RemotePluginInfo:
        """解析 MCP server 列表数据（不包含连接信息）"""
        return RemotePluginInfo(
            plugin_id=item.get("id", ""),
            name=item.get("chinese_name") or item.get("name", ""),
            description=item.get("description", ""),
            version="latest",
            author=item.get("publisher", ""),
            icon=item.get("logo_url"),
            plugin_type="mcp",
            tags=item.get("tags", []),
            downloads=item.get("view_count"),
            manifest_url=None,
            download_url="",  # 列表不包含连接信息
            created_at=None,
            updated_at=None,
        )

    def _parse_mcp_detail(self, item: dict) -> RemotePluginInfo:
        """解析 MCP server 详情数据（包含连接信息）"""
        # 从 operational_urls 获取连接信息
        server_url = ""
        transport = "streamable_http"
        auth_required = False

        operational_urls = item.get("operational_urls", [])
        if operational_urls:
            # 取第一个可用的连接
            first_url = operational_urls[0]
            server_url = first_url.get("url", "")
            transport = first_url.get("transport_type", "streamable_http")
            auth_required = first_url.get("auth_required", False)

        return RemotePluginInfo(
            plugin_id=item.get("id", ""),
            name=item.get("chinese_name") or item.get("name", ""),
            description=item.get("description", ""),
            version="latest",
            author=item.get("author") or item.get("publisher", ""),
            icon=item.get("logo_url"),
            plugin_type="mcp",
            tags=item.get("tags", []),
            downloads=item.get("view_count"),
            manifest_url=None,
            download_url=server_url,
            created_at=None,
            updated_at=None,
            skill_metadata={
                "transport_type": transport,
                "auth_required": auth_required,
                "is_hosted": item.get("is_hosted", False),
                "is_verified": item.get("is_verified", False),
            },
        )

    def _parse_datetime(self, value: str | None) -> datetime | None:
        """解析时间字符串"""
        if not value:
            return None

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
