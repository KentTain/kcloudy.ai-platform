"""ModelScope 模型市场适配器"""

from __future__ import annotations

import asyncio
import hashlib
import os
import time
import tempfile
import zipfile
from datetime import datetime
from typing import TYPE_CHECKING, Any

import httpx
import yaml
from loguru import logger

from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class ModelScopeAdapter(MarketplaceAdapter):
    """ModelScope 模型市场适配器"""

    API_BASE = "https://modelscope.cn/api/v1"

    @property
    def market_type(self) -> str:
        return "modelscope"

    def _build_headers(self, config: dict) -> dict[str, str]:
        """构建请求头"""
        headers = {"Accept": "application/json"}
        auth_config = config.get("auth_config", {})
        api_token = auth_config.get("api_token", "")
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        return headers

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        headers = self._build_headers(config)
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/models",
                    headers=headers,
                    params={"Page": 1, "PageSize": 1},
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
            logger.error(f"测试 ModelScope 市场连接失败: {e}")
            return MarketplaceTestResult(
                success=False, message=f"连接异常: {str(e)}"
            )

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        headers = self._build_headers(config)
        params: dict[str, Any] = {"Page": page, "PageSize": page_size}
        if keyword:
            params["Name"] = keyword
        if plugin_type:
            params["Task"] = plugin_type
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/models", headers=headers, params=params
                )
                response.raise_for_status()
                data = response.json()
            plugins = [
                p
                for item in data.get("Data", {}).get("Models", [])
                if (p := self._parse_model(item)) is not None
            ]
            return plugins, data.get("Data", {}).get("TotalCount", 0)
        except httpx.TimeoutException:
            logger.error(f"获取 ModelScope 插件列表超时")
            return [], 0
        except httpx.HTTPStatusError as e:
            logger.error(f"获取 ModelScope 插件列表失败: HTTP {e.response.status_code}")
            return [], 0
        except Exception as e:
            logger.error(f"获取 ModelScope 插件列表异常: {e}")
            return [], 0

    async def get_plugin(
        self, config: dict, plugin_id: str
    ) -> RemotePluginInfo | None:
        headers = self._build_headers(config)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/models/{plugin_id}", headers=headers
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return self._parse_model(response.json().get("Data", {}))
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
        auth_config = config.get("auth_config", {})
        api_token = auth_config.get("api_token", "")
        zip_data, checksum = await asyncio.to_thread(
            self._download_plugin_sync, plugin_id, version, api_token
        )
        return zip_data, checksum

    def _download_plugin_sync(
        self,
        plugin_id: str,
        version: str | None,
        api_token: str,
    ) -> tuple[bytes, str]:
        """同步下载插件包（阻塞 IO，由 asyncio.to_thread 调用）"""
        from modelscope import snapshot_download

        # 需要排除的文件后缀（SDK 缓存/临时文件）
        _EXCLUDED_SUFFIXES = (".crdownload", ".cache", ".tmp")

        with tempfile.TemporaryDirectory() as temp_dir:
            local_dir = snapshot_download(
                model_id=plugin_id,
                revision=version or "master",
                api_token=api_token,
                cache_dir=temp_dir,
            )
            manifest = {
                "author": plugin_id.split("/")[0],
                "name": plugin_id.split("/")[1] if "/" in plugin_id else plugin_id,
                "version": version or "latest",
                "type": "model",
                "description": f"ModelScope model: {plugin_id}",
            }
            zip_path = os.path.join(temp_dir, "plugin.zip")
            with zipfile.ZipFile(zip_path, "w") as zf:
                for root, dirs, files in os.walk(local_dir):
                    # 排除隐藏目录（以 . 开头）
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    for file in files:
                        # 排除临时/缓存文件
                        if file.endswith(_EXCLUDED_SUFFIXES):
                            continue
                        zf.write(
                            os.path.join(root, file),
                            os.path.relpath(
                                os.path.join(root, file), local_dir
                            ),
                        )
                zf.writestr("manifest.yaml", yaml.dump(manifest))
            with open(zip_path, "rb") as f:
                zip_data = f.read()
        checksum = hashlib.sha256(zip_data).hexdigest()
        return zip_data, checksum

    async def check_updates(
        self,
        config: dict,
        plugins: Sequence[dict],
    ) -> Sequence[PluginUpdateInfo]:
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
                    results.append(
                        PluginUpdateInfo(
                            plugin_id=plugin_id,
                            current_version=current_version or "",
                            latest_version=remote.version,
                            has_update=has_update,
                            changelog=None,
                        )
                    )
            except Exception as e:
                logger.warning(f"检查插件更新失败: {plugin_id}, 错误: {e}")
        return results

    def _parse_model(self, item: dict) -> RemotePluginInfo | None:
        """解析模型数据"""
        namespace = item.get("Namespace", "")
        name = item.get("Name", "")
        # namespace 和 name 都为空时无法构建有效 plugin_id，跳过
        if not namespace and not name:
            return None
        return RemotePluginInfo(
            plugin_id=f"{namespace}/{name}",
            name=item.get("ChineseName", name) or name,
            description=item.get("Description", ""),
            version=item.get("Version", "latest"),
            author=namespace,
            icon=None,
            plugin_type="model",
            tags=item.get("Tags", []),
            downloads=item.get("Downloads"),
            manifest_url=None,
            download_url=f"modelscope://{namespace}/{name}",
            created_at=self._parse_datetime(item.get("CreateTime")),
            updated_at=self._parse_datetime(item.get("UpdateTime")),
        )

    def _parse_datetime(self, value: str | None) -> datetime | None:
        """解析日期时间"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
