"""ModelScope Skill 市场适配器

符合 ModelScope OpenAPI 规范（https://modelscope.cn/docs/openapi）。

关键特性：
- Skill 不是传统插件包，而是配置清单和安装指令
- source_url 是源码地址，不能用于下载
- Skill 通过 CLI 命令安装，无独立的下载 URL
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

import httpx
from loguru import logger

from tenant.services.marketplace.git_sync_service import GitSyncService
from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)
from tenant.services.marketplace.skill_scanner import SkillScanner

if TYPE_CHECKING:
    from collections.abc import Sequence


class ModelScopeSkillAdapter(MarketplaceAdapter):
    """ModelScope Skill 市场适配器（符合官方 OpenAPI 规范）"""

    API_BASE = "https://modelscope.cn/openapi/v1"

    def __init__(
        self,
        git_sync: GitSyncService | None = None,
        scanner: SkillScanner | None = None,
    ):
        self.git_sync = git_sync or GitSyncService()
        self.scanner = scanner or SkillScanner()

    @property
    def market_type(self) -> str:
        """市场类型标识"""
        return "modelscope-skill"

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
        return config.get("url", self.API_BASE)

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接"""
        headers = self._build_headers(config)
        base_url = self._get_base_url(config)
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{base_url}/skills",
                    headers=headers,
                    params={"page_number": 1, "page_size": 1},
                )
                latency_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    total = data.get("data", {}).get("total", 0)
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
            logger.error(f"测试 ModelScope Skill 市场连接失败: {e}")
            return MarketplaceTestResult(success=False, message=f"连接异常: {str(e)}")

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取远程 Skill 列表"""
        headers = self._build_headers(config)
        base_url = self._get_base_url(config)

        params: dict[str, Any] = {"page_number": page, "page_size": page_size}
        if keyword:
            params["search"] = keyword

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/skills",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        # 解析响应：data.skills, data.total
        skills_data = data.get("data", {}).get("skills", [])
        total = data.get("data", {}).get("total", 0)
        plugins = [self._parse_skill(item) for item in skills_data]

        return plugins, total

    async def get_plugin(self, config: dict, plugin_id: str) -> RemotePluginInfo | None:
        """获取单个 Skill 详情"""
        headers = self._build_headers(config)
        base_url = self._get_base_url(config)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{base_url}/skills/{plugin_id}",
                    headers=headers,
                )

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                data = response.json()
                return self._parse_skill(data.get("data", {}))

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
        """下载 Skill 包

        当 skill_metadata 中有 source_url 时，使用 git sparse-checkout
        拉取并 ZIP 打包；否则兜底返回声明清单。
        """
        skill_info = await self.get_plugin(config, plugin_id)
        if not skill_info:
            raise ValueError(f"Skill {plugin_id} not found")

        metadata = skill_info.skill_metadata or {}
        source_url = metadata.get("source_url", "")

        if not source_url:
            return self._generate_declaration(skill_info)

        # 有 source_url：通过 GitSyncService 拉取并打包
        repo_url, ref, subdir = self.git_sync.parse_source_url(source_url)
        skill_dir, commit_sha = await self.git_sync.sync_repo(repo_url, ref=ref, subdir=subdir)
        skills = self.scanner.scan_skills(skill_dir)
        if not skills:
            raise ValueError(f"No SKILL.md found in {source_url}")
        return self.scanner.zip_skill(skills[0])

    def _generate_declaration(self, skill_info: RemotePluginInfo) -> tuple[bytes, str]:
        """兜底：返回 JSON 声明清单

        当 source_url 不可用时，生成包含安装指令的声明清单。
        """
        metadata = skill_info.skill_metadata or {}
        category = metadata.get("category", "")

        declaration = {
            "skill": {
                "skill_type": self._infer_skill_type(category),
                "runtime": "none",
            },
            "metadata": {
                "name": skill_info.name,
                "description": skill_info.description,
                "version": skill_info.version,
                "author": skill_info.author,
                "tags": skill_info.tags,
            },
            "install": {
                "source_url": metadata.get("source_url", ""),
                "commands": metadata.get("install_commands", []),
            },
        }

        data = json.dumps(declaration, ensure_ascii=False, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(data).hexdigest()
        return data, checksum

    async def check_updates(
        self,
        config: dict,
        plugins: Sequence[dict],
    ) -> Sequence[PluginUpdateInfo]:
        """检查 Skill 更新"""
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
                logger.warning(f"检查 Skill 更新失败: {plugin_id}, 错误: {e}")

        return results

    def _parse_skill(self, item: dict) -> RemotePluginInfo:
        """解析 Skill 数据"""
        return RemotePluginInfo(
            plugin_id=item.get("id", ""),
            name=item.get("display_name", ""),
            description=item.get("description", ""),
            version="latest",
            author=item.get("owner") or item.get("developer", ""),
            icon=item.get("logo_url"),
            plugin_type="skill",
            tags=item.get("tags", []),
            downloads=item.get("downloads"),
            manifest_url=None,
            download_url="",  # Skill 没有下载 URL
            created_at=self._parse_datetime(item.get("last_modified")),
            updated_at=self._parse_datetime(item.get("file_last_modified")),
            skill_metadata={
                "category": item.get("category", ""),
                "developer": item.get("developer", ""),
                "source_url": item.get("source_url", ""),
                "license": item.get("license", ""),
                "view_count": item.get("view_count", 0),
                "install_commands": [],  # 详情接口才有
            },
        )

    def _infer_skill_type(self, category: str) -> str:
        """从 category 推断 skill_type"""
        # 根据 category 判断
        knowledge_categories = ["knowledge-base", "documentation"]
        if category in knowledge_categories:
            return "knowledge"
        return "script"

    def _parse_datetime(self, value: str | None) -> datetime | None:
        """解析时间字符串"""
        if not value:
            return None

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
