"""Dify 插件市场适配器"""

from __future__ import annotations

import hashlib
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


class DifyAdapter(MarketplaceAdapter):
    """Dify 插件市场适配器"""

    @property
    def market_type(self) -> str:
        return "dify"

    def _build_headers(self, config: dict) -> dict[str, str]:
        """构建请求头"""
        headers = {"Accept": "application/json"}
        auth_type = config.get("auth_type", "none")
        auth_config = config.get("auth_config", {})

        if auth_type == "api_key":
            api_key = auth_config.get("api_key", "")
            header_name = auth_config.get("header_name", "X-API-Key")
            if api_key:
                headers[header_name] = api_key
        elif auth_type == "token":
            token = auth_config.get("token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        return headers

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接"""
        url = config.get("url", "")
        if not url:
            return MarketplaceTestResult(success=False, message="市场地址不能为空")

        headers = self._build_headers(config)
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{url.rstrip('/')}/plugins", headers=headers, params={"page": 1, "page_size": 1})
                latency_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    total = data.get("total", 0)
                    return MarketplaceTestResult(
                        success=True,
                        message="连接成功",
                        plugin_count=total,
                        latency_ms=latency_ms,
                    )
                else:
                    return MarketplaceTestResult(
                        success=False,
                        message=f"连接失败: HTTP {response.status_code}",
                        latency_ms=latency_ms,
                    )
        except httpx.TimeoutException:
            return MarketplaceTestResult(success=False, message="连接超时")
        except Exception as e:
            logger.error(f"测试 Dify 市场连接失败: {e}")
            return MarketplaceTestResult(success=False, message=f"连接异常: {str(e)}")

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取远程插件列表"""
        url = config.get("url", "")
        if not url:
            return [], 0

        headers = self._build_headers(config)

        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if keyword:
            params["keyword"] = keyword
        if plugin_type:
            params["type"] = plugin_type

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{url.rstrip('/')}/plugins", headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

            plugins = []
            for item in data.get("plugins", []):
                plugins.append(self._parse_plugin(item, url))

            return plugins, data.get("total", 0)
        except httpx.TimeoutException:
            logger.error(f"获取 Dify 插件列表超时: {url}")
            return [], 0
        except httpx.HTTPStatusError as e:
            logger.error(f"获取 Dify 插件列表失败: HTTP {e.response.status_code}")
            return [], 0
        except Exception as e:
            logger.error(f"获取 Dify 插件列表异常: {e}")
            return [], 0

    async def get_plugin(self, config: dict, plugin_id: str) -> RemotePluginInfo | None:
        """获取单个插件详情"""
        url = config.get("url", "")
        headers = self._build_headers(config)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{url.rstrip('/')}/plugins/{plugin_id}", headers=headers)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()
                return self._parse_plugin(data.get("plugin", data), url)
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
        """下载插件包"""
        url = config.get("url", "")
        headers = self._build_headers(config)

        download_url = f"{url.rstrip('/')}/plugins/{plugin_id}/download"
        if version:
            download_url += f"?version={version}"

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(download_url, headers=headers)
            response.raise_for_status()
            data = response.content
            checksum = hashlib.sha256(data).hexdigest()
            return data, checksum

    async def check_updates(
        self,
        config: dict,
        plugins: Sequence[dict],
    ) -> Sequence[PluginUpdateInfo]:
        """检查插件更新"""
        url = config.get("url", "")
        headers = self._build_headers(config)

        results = []
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
                logger.warning(f"检查插件更新失败: {plugin_id}, 错误: {e}")

        return results

    def _parse_plugin(self, item: dict, base_url: str) -> RemotePluginInfo:
        """解析插件数据"""
        author = item.get("author", "")
        name = item.get("name", "")
        plugin_id = item.get("plugin_id", f"{author}/{name}")

        return RemotePluginInfo(
            plugin_id=plugin_id,
            name=item.get("label", {}).get("en_US", name) or name,
            description=item.get("description", {}).get("en_US", ""),
            version=item.get("version", "0.0.1"),
            author=author,
            icon=item.get("icon"),
            plugin_type=item.get("type", "tool"),
            tags=item.get("tags", []),
            downloads=item.get("downloads"),
            manifest_url=item.get("manifest_url"),
            download_url=f"{base_url.rstrip('/')}/plugins/{plugin_id}/download",
            created_at=self._parse_datetime(item.get("created_at")),
            updated_at=self._parse_datetime(item.get("updated_at")),
        )

    def _parse_datetime(self, value: str | None) -> datetime | None:
        """解析日期时间"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
