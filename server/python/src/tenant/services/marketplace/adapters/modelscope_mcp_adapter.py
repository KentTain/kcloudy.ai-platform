"""ModelScope MCP 市场适配器

魔搭社区提供独立的 MCP server 市场，与模型市场、Skill 市场并列。
本适配器仅负责 MCP server 资源的浏览与同步，不复用 ModelScopeAdapter
（后者只覆盖模型）。
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
    """ModelScope MCP 市场适配器（兼容 modelscope.cn/mcp API）"""

    @property
    def market_type(self) -> str:
        """市场类型标识"""
        return "modelscope-mcp"

    def _build_headers(self, config: dict) -> dict[str, str]:
        """构建请求头"""
        headers = {"Accept": "application/json"}
        auth_config = config.get("auth_config", {})
        api_token = auth_config.get("api_token", "")
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        return headers

    def _get_base_url(self, config: dict) -> str:
        """获取 API 基础 URL"""
        return config.get("url", "https://modelscope.cn/api/v1")

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接"""
        headers = self._build_headers(config)
        base_url = self._get_base_url(config)
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{base_url}/mcpServers",
                    headers=headers,
                    params={"PageNumber": 1, "PageSize": 1},
                )
                latency_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    total = data.get("Data", {}).get("TotalCount", 0)
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
        params: dict[str, Any] = {"PageNumber": page, "PageSize": page_size}

        if keyword:
            params["Name"] = keyword

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/mcpServers",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        servers_data = data.get("Data", {}).get("McpServers", []) or data.get("Data", {}).get("Servers", [])
        total = data.get("Data", {}).get("TotalCount", 0)
        plugins = [self._parse_mcp(item) for item in servers_data]

        return plugins, total

    async def get_plugin(self, config: dict, plugin_id: str) -> RemotePluginInfo | None:
        """获取单个 MCP server 详情"""
        headers = self._build_headers(config)
        base_url = self._get_base_url(config)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{base_url}/mcpServers/{plugin_id}",
                    headers=headers,
                )

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                data = response.json()
                return self._parse_mcp(data.get("Data", {}))

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

        manifest = {
            "mcp": {
                "server_url": remote_info.download_url,
                "transport": self._extract_transport(remote_info),
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
        """解析 MCP server 数据"""
        plugin_id = item.get("Id", "") or item.get("Name", "")
        name = item.get("ChineseName") or item.get("Name", "")
        author = item.get("Owner", "")
        # MCP server 的访问端点
        server_url = item.get("ServerUrl") or item.get("Endpoint") or item.get("Url", "")
        transport = item.get("Transport") or item.get("Protocol", "streamable_http")

        return RemotePluginInfo(
            plugin_id=plugin_id,
            name=name,
            description=item.get("Description", ""),
            version=item.get("Version", "latest"),
            author=author,
            icon=item.get("Logo"),
            plugin_type="mcp",  # MCP 市场的插件类型固定为 "mcp"
            tags=item.get("Tags", []),
            downloads=item.get("Downloads"),
            manifest_url=None,
            download_url=server_url,
            created_at=self._parse_datetime(item.get("CreateTime")),
            updated_at=self._parse_datetime(item.get("UpdateTime")),
        )

    def _extract_transport(self, info: RemotePluginInfo) -> str:
        """从下载 URL 推导传输方式"""
        url = (info.download_url or "").lower()
        if url.startswith("ws://") or url.startswith("wss://"):
            return "websocket"
        if "/sse" in url:
            return "sse"
        return "streamable_http"

    def _parse_datetime(self, value: str | None) -> datetime | None:
        """解析时间字符串"""
        if not value:
            return None

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
