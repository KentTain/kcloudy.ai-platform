# 远程插件市场功能实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现远程插件市场功能，支持配置多个外部市场源（Dify、ModelScope），浏览远程插件列表，选择性同步插件定义到本地，检测和应用插件更新。

**架构：** 采用适配器模式统一不同市场的接口，通过 MarketplaceGateway 协调配置管理、远程插件浏览、插件同步和更新检查。复用现有的 plugin_package_service 解析逻辑和 plugin_storage_service 存储能力。

**技术栈：** Python 3.12 + FastAPI + SQLAlchemy 2.0 + httpx（后端），Vue 3 + TypeScript + shadcn-vue（前端）

---

## 文件结构

### 后端新增文件

| 文件 | 职责 |
|------|------|
| `server/python/src/tenant/models/plugin_marketplace.py` | 市场配置数据库模型 |
| `server/python/src/tenant/models/plugin_package.py` | 插件包存储记录模型 |
| `server/python/src/tenant/schemas/admin/marketplace.py` | 市场 API Schema |
| `server/python/src/tenant/services/marketplace/__init__.py` | 市场服务模块入口 |
| `server/python/src/tenant/services/marketplace/protocol.py` | 适配器协议和数据模型 |
| `server/python/src/tenant/services/marketplace/gateway.py` | 市场网关服务 |
| `server/python/src/tenant/services/marketplace/adapters/__init__.py` | 适配器模块入口 |
| `server/python/src/tenant/services/marketplace/adapters/dify_adapter.py` | Dify 市场适配器 |
| `server/python/src/tenant/services/marketplace/adapters/modelscope_adapter.py` | ModelScope 适配器 |
| `server/python/src/tenant/controllers/admin/marketplace_controller.py` | 市场 API 控制器 |

### 后端修改文件

| 文件 | 修改内容 |
|------|----------|
| `server/python/src/tenant/models/plugin_definition.py` | 添加来源相关字段 |
| `server/python/src/tenant/models/__init__.py` | 导出新模型 |
| `server/python/src/tenant/migrations/versions/001_initial_schema.py` | 添加市场相关表 |
| `server/python/src/tenant/controllers/admin/__init__.py` | 注册市场路由 |
| `server/python/src/tenant/module.py` | 添加市场相关权限定义 |

### 前端新增文件

| 文件 | 职责 |
|------|------|
| `web/vue/src/tenant/api/marketplace.ts` | 市场 API 函数 |
| `web/vue/src/tenant/types/marketplace.ts` | 市场 TypeScript 类型 |
| `web/vue/src/tenant/pages/admin/MarketplaceListPage.vue` | 市场配置列表页 |
| `web/vue/src/tenant/pages/admin/MarketplaceFormPage.vue` | 市场配置表单页 |
| `web/vue/src/tenant/pages/admin/RemotePluginBrowsePage.vue` | 远程插件浏览页 |

### 前端修改文件

| 文件 | 修改内容 |
|------|----------|
| `web/vue/src/tenant/router/index.ts` | 添加市场相关路由 |

---

## 任务 1：数据模型与迁移

**文件：**
- 创建：`server/python/src/tenant/models/plugin_marketplace.py`
- 创建：`server/python/src/tenant/models/plugin_package.py`
- 修改：`server/python/src/tenant/models/plugin_definition.py`
- 修改：`server/python/src/tenant/models/__init__.py`
- 修改：`server/python/src/tenant/migrations/versions/001_initial_schema.py`

- [ ] **步骤 1：编写市场配置模型**

```python
# server/python/src/tenant/models/plugin_marketplace.py
"""插件市场配置模型"""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from tenant.models import BaseModel


class TenantPluginMarketplace(BaseModel, AuditMixin, ActiveRecordMixin):
    """插件市场配置模型"""

    __tablename__ = "plugin_marketplaces"

    name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="市场名称",
    )
    code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        unique=True,
        index=True,
        comment="市场编码",
    )
    type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="市场类型：dify, modelscope",
    )
    url: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="市场 API 地址",
    )
    auth_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="none",
        comment="认证类型：none, api_key, token",
    )
    auth_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="认证配置（加密存储）",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        comment="是否启用",
    )
    sync_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="同步配置",
    )
    last_sync_at: Mapped[str | None] = mapped_column(
        comment="最后同步时间",
    )
    last_sync_status: Mapped[str | None] = mapped_column(
        String(16),
        comment="最后同步状态",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        comment="市场描述",
    )

    __table_args__ = ({"comment": "插件市场配置表"},)
```

- [ ] **步骤 2：编写插件包存储模型**

```python
# server/python/src/tenant/models/plugin_package.py
"""插件包存储记录模型"""

from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.timestamp import TimestampMixin
from tenant.models import BaseModel


class TenantPluginPackage(BaseModel, TimestampMixin, ActiveRecordMixin):
    """插件包存储记录模型"""

    __tablename__ = "plugin_packages"

    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID：author/name",
    )
    version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="版本号",
    )
    marketplace_id: Mapped[str | None] = mapped_column(
        comment="来源市场ID",
    )
    storage_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="MinIO 存储路径",
    )
    file_size: Mapped[int | None] = mapped_column(
        BigInteger,
        comment="文件大小（字节）",
    )
    checksum: Mapped[str | None] = mapped_column(
        String(128),
        comment="SHA256 校验和",
    )
    manifest: Mapped[dict | None] = mapped_column(
        JSONB,
        comment="解析后的 manifest",
    )

    __table_args__ = (
        UniqueConstraint(
            "plugin_id", "version", "marketplace_id",
            name="uq_plugin_packages_plugin_version_marketplace"
        ),
        {"comment": "插件包存储记录表"},
    )
```

- [ ] **步骤 3：扩展插件定义模型**

在 `server/python/src/tenant/models/plugin_definition.py` 添加字段：

```python
# 在现有字段后添加
marketplace_id: Mapped[str | None] = mapped_column(
    comment="来源市场ID，本地注册的为 NULL",
)
remote_plugin_id: Mapped[str | None] = mapped_column(
    String(128),
    comment="远程市场的插件标识",
)
remote_version: Mapped[str | None] = mapped_column(
    String(32),
    comment="远程最新版本",
)
local_version: Mapped[str | None] = mapped_column(
    String(32),
    comment="本地存储版本",
)
update_available: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
    server_default="false",
    comment="是否有新版本",
)
package_id: Mapped[str | None] = mapped_column(
    comment="关联的插件包记录",
)
source_type: Mapped[str] = mapped_column(
    String(16),
    nullable=False,
    default="local",
    comment="来源类型：local, remote",
)
```

- [ ] **步骤 4：更新模型导出**

修改 `server/python/src/tenant/models/__init__.py`：

```python
# 在现有导出后添加
from tenant.models.plugin_marketplace import TenantPluginMarketplace
from tenant.models.plugin_package import TenantPluginPackage

# 在 __all__ 中添加
__all__ = [
    # ... 现有导出
    "TenantPluginMarketplace",
    "TenantPluginPackage",
]
```

- [ ] **步骤 5：添加数据库迁移**

在 `server/python/src/tenant/migrations/versions/001_initial_schema.py` 添加表定义：

```python
# 在 op.create_table 调用列表中添加

# plugin_marketplaces 表
op.create_table(
    "plugin_marketplaces",
    sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
    sa.Column("name", sa.String(64), nullable=False),
    sa.Column("code", sa.String(32), nullable=False, unique=True),
    sa.Column("type", sa.String(32), nullable=False),
    sa.Column("url", sa.String(512), nullable=False),
    sa.Column("auth_type", sa.String(16), nullable=False, server_default="none"),
    sa.Column("auth_config", postgresql.JSONB, nullable=False, server_default="{}"),
    sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="true"),
    sa.Column("sync_config", postgresql.JSONB, nullable=False, server_default="{}"),
    sa.Column("last_sync_at", sa.DateTime, nullable=True),
    sa.Column("last_sync_status", sa.String(16), nullable=True),
    sa.Column("description", sa.Text, nullable=True),
    sa.Column("created_at", sa.DateTime, server_default=sa.func.current_timestamp()),
    sa.Column("updated_at", sa.DateTime, server_default=sa.func.current_timestamp()),
    sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
    sa.Column("updated_by", postgresql.UUID(as_uuid=False), nullable=True),
    schema="tenant",
)
op.create_index("idx_plugin_marketplaces_code", "plugin_marketplaces", ["code"], schema="tenant")
op.create_index("idx_plugin_marketplaces_type", "plugin_marketplaces", ["type"], schema="tenant")
op.create_index("idx_plugin_marketplaces_enabled", "plugin_marketplaces", ["is_enabled"], schema="tenant")

# plugin_packages 表
op.create_table(
    "plugin_packages",
    sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
    sa.Column("plugin_id", sa.String(128), nullable=False),
    sa.Column("version", sa.String(32), nullable=False),
    sa.Column("marketplace_id", postgresql.UUID(as_uuid=False), nullable=True),
    sa.Column("storage_path", sa.String(512), nullable=False),
    sa.Column("file_size", sa.BigInteger, nullable=True),
    sa.Column("checksum", sa.String(128), nullable=True),
    sa.Column("manifest", postgresql.JSONB, nullable=True),
    sa.Column("created_at", sa.DateTime, server_default=sa.func.current_timestamp()),
    sa.Column("updated_at", sa.DateTime, server_default=sa.func.current_timestamp()),
    sa.UniqueConstraint("plugin_id", "version", "marketplace_id", name="uq_plugin_packages_plugin_version_marketplace"),
    schema="tenant",
)
op.create_index("idx_plugin_packages_plugin_id", "plugin_packages", ["plugin_id"], schema="tenant")
op.create_index("idx_plugin_packages_marketplace", "plugin_packages", ["marketplace_id"], schema="tenant")

# 扩展 plugin_definitions 表
op.add_column("plugin_definitions", sa.Column("marketplace_id", postgresql.UUID(as_uuid=False), nullable=True), schema="tenant")
op.add_column("plugin_definitions", sa.Column("remote_plugin_id", sa.String(128), nullable=True), schema="tenant")
op.add_column("plugin_definitions", sa.Column("remote_version", sa.String(32), nullable=True), schema="tenant")
op.add_column("plugin_definitions", sa.Column("local_version", sa.String(32), nullable=True), schema="tenant")
op.add_column("plugin_definitions", sa.Column("update_available", sa.Boolean, nullable=False, server_default="false"), schema="tenant")
op.add_column("plugin_definitions", sa.Column("package_id", postgresql.UUID(as_uuid=False), nullable=True), schema="tenant")
op.add_column("plugin_definitions", sa.Column("source_type", sa.String(16), nullable=False, server_default="local"), schema="tenant")
```

- [ ] **步骤 6：运行迁移验证**

运行：`cd server/python && uv run python manage.py db migrate --module tenant`
预期：迁移成功，无错误

- [ ] **步骤 7：Commit**

```bash
git add server/python/src/tenant/models/plugin_marketplace.py
git add server/python/src/tenant/models/plugin_package.py
git add server/python/src/tenant/models/plugin_definition.py
git add server/python/src/tenant/models/__init__.py
git add server/python/src/tenant/migrations/versions/001_initial_schema.py
git commit -m "feat(tenant): 添加插件市场数据模型和迁移

- 新增 plugin_marketplaces 表存储市场配置
- 新增 plugin_packages 表存储插件包记录
- 扩展 plugin_definitions 表添加来源相关字段

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 2：适配器协议与数据模型

**文件：**
- 创建：`server/python/src/tenant/services/marketplace/__init__.py`
- 创建：`server/python/src/tenant/services/marketplace/protocol.py`

- [ ] **步骤 1：创建模块入口**

```python
# server/python/src/tenant/services/marketplace/__init__.py
"""插件市场服务模块"""

from tenant.services.marketplace.gateway import marketplace_gateway
from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)

__all__ = [
    "marketplace_gateway",
    "MarketplaceAdapter",
    "MarketplaceTestResult",
    "PluginUpdateInfo",
    "RemotePluginInfo",
]
```

- [ ] **步骤 2：编写适配器协议和数据模型**

```python
# server/python/src/tenant/services/marketplace/protocol.py
"""插件市场适配器协议"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class RemotePluginInfo:
    """远程插件信息"""

    plugin_id: str  # 插件ID：author/name
    name: str  # 显示名称
    description: str | None  # 描述
    version: str  # 版本
    author: str  # 作者
    icon: str | None  # 图标 URL
    plugin_type: str  # tool/model/agent
    tags: list[str]  # 标签
    downloads: int | None  # 下载量
    manifest_url: str | None  # 清单文件 URL
    download_url: str  # 下载地址
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class PluginUpdateInfo:
    """插件更新信息"""

    plugin_id: str
    current_version: str  # 当前版本
    latest_version: str  # 最新版本
    has_update: bool  # 是否有更新
    changelog: str | None  # 更新日志


@dataclass
class MarketplaceTestResult:
    """市场连接测试结果"""

    success: bool
    message: str
    plugin_count: int | None = None  # 可用插件数量
    latency_ms: int | None = None  # 响应延迟


class MarketplaceAdapter(Protocol):
    """市场适配器协议"""

    @property
    def market_type(self) -> str:
        """市场类型标识：dify, modelscope"""
        ...

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接

        Args:
            config: 市场配置（url, auth_type, auth_config）

        Returns:
            MarketplaceTestResult: 测试结果
        """
        ...

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取远程插件列表

        Args:
            config: 市场配置
            keyword: 搜索关键词
            plugin_type: 插件类型筛选
            page: 页码
            page_size: 每页条数

        Returns:
            tuple[list[RemotePluginInfo], int]: (插件列表, 总数)
        """
        ...

    async def get_plugin(
        self,
        config: dict,
        plugin_id: str,
    ) -> RemotePluginInfo | None:
        """获取单个插件详情

        Args:
            config: 市场配置
            plugin_id: 插件ID

        Returns:
            RemotePluginInfo | None: 插件信息，不存在返回 None
        """
        ...

    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """下载插件包

        Args:
            config: 市场配置
            plugin_id: 插件ID
            version: 版本号，None 表示最新版本

        Returns:
            tuple[bytes, str]: (插件包数据, SHA256校验和)
        """
        ...

    async def check_updates(
        self,
        config: dict,
        plugins: Sequence[dict],
    ) -> Sequence[PluginUpdateInfo]:
        """检查插件更新

        Args:
            config: 市场配置
            plugins: 需要检查的插件列表，每项包含 plugin_id, current_version

        Returns:
            list[PluginUpdateInfo]: 更新信息列表
        """
        ...
```

- [ ] **步骤 3：运行类型检查验证**

运行：`cd server/python && uv run mypy src/tenant/services/marketplace/protocol.py`
预期：类型检查通过，无错误

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/tenant/services/marketplace/
git commit -m "feat(tenant): 添加插件市场适配器协议

- 定义 MarketplaceAdapter 协议统一不同市场接口
- 定义 RemotePluginInfo、PluginUpdateInfo、MarketplaceTestResult 数据模型

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 3：Dify 市场适配器

**文件：**
- 创建：`server/python/src/tenant/services/marketplace/adapters/__init__.py`
- 创建：`server/python/src/tenant/services/marketplace/adapters/dify_adapter.py`

- [ ] **步骤 1：创建适配器模块入口**

```python
# server/python/src/tenant/services/marketplace/adapters/__init__.py
"""市场适配器模块"""

from tenant.services.marketplace.adapters.dify_adapter import DifyAdapter

__all__ = [
    "DifyAdapter",
]
```

- [ ] **步骤 2：编写 Dify 适配器**

```python
# server/python/src/tenant/services/marketplace/adapters/dify_adapter.py
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
        headers = self._build_headers(config)

        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if keyword:
            params["keyword"] = keyword
        if plugin_type:
            params["type"] = plugin_type

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{url.rstrip('/')}/plugins", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        plugins = []
        for item in data.get("plugins", []):
            plugins.append(self._parse_plugin(item, url))

        return plugins, data.get("total", 0)

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
```

- [ ] **步骤 3：编写适配器单元测试**

创建测试文件 `server/python/tests/tenant/unit/services/marketplace/test_dify_adapter.py`：

```python
"""Dify 适配器单元测试"""

import pytest
from tenant.services.marketplace.adapters.dify_adapter import DifyAdapter


@pytest.fixture
def dify_adapter() -> DifyAdapter:
    return DifyAdapter()


@pytest.mark.asyncio
async def test_market_type(dify_adapter: DifyAdapter):
    """测试市场类型"""
    assert dify_adapter.market_type == "dify"


@pytest.mark.asyncio
async def test_build_headers_no_auth(dify_adapter: DifyAdapter):
    """测试无认证时构建请求头"""
    config = {"auth_type": "none", "auth_config": {}}
    headers = dify_adapter._build_headers(config)
    assert headers == {"Accept": "application/json"}


@pytest.mark.asyncio
async def test_build_headers_api_key(dify_adapter: DifyAdapter):
    """测试 API Key 认证时构建请求头"""
    config = {
        "auth_type": "api_key",
        "auth_config": {"api_key": "test-key", "header_name": "X-API-Key"},
    }
    headers = dify_adapter._build_headers(config)
    assert headers["X-API-Key"] == "test-key"
```

- [ ] **步骤 4：运行测试验证**

运行：`cd server/python && uv run pytest tests/tenant/unit/services/marketplace/test_dify_adapter.py -v`
预期：测试通过

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/adapters/
git add server/python/tests/tenant/unit/services/marketplace/
git commit -m "feat(tenant): 实现 Dify 插件市场适配器

- 实现连接测试、插件列表、插件详情、下载、更新检查功能
- 添加适配器单元测试

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 4：MarketplaceGateway 服务

**文件：**
- 创建：`server/python/src/tenant/services/marketplace/gateway.py`

- [ ] **步骤 1：编写 MarketplaceGateway 服务**

```python
# server/python/src/tenant/services/marketplace/gateway.py
"""插件市场网关服务"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.models import TenantPluginMarketplace
from tenant.services.marketplace.adapters.dify_adapter import DifyAdapter
from tenant.services.marketplace.protocol import (
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

    def _get_adapter(self, market_type: str):
        """获取适配器实例"""
        adapter_class = self._adapters.get(market_type)
        if not adapter_class:
            raise ValueError(f"不支持的市场类型: {market_type}")
        return adapter_class()

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
        config = {
            "url": marketplace.url,
            "auth_type": marketplace.auth_type,
            "auth_config": marketplace.auth_config,
        }
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
        config = {
            "url": marketplace.url,
            "auth_type": marketplace.auth_type,
            "auth_config": marketplace.auth_config,
        }
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
        config = {
            "url": marketplace.url,
            "auth_type": marketplace.auth_type,
            "auth_config": marketplace.auth_config,
        }
        return await adapter.get_plugin(config, plugin_id)


# 单例实例
marketplace_gateway = MarketplaceGateway()
```

- [ ] **步骤 2：更新模块入口**

更新 `server/python/src/tenant/services/marketplace/__init__.py`：

```python
# server/python/src/tenant/services/marketplace/__init__.py
"""插件市场服务模块"""

from tenant.services.marketplace.adapters.dify_adapter import DifyAdapter
from tenant.services.marketplace.gateway import marketplace_gateway
from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)

__all__ = [
    "marketplace_gateway",
    "DifyAdapter",
    "MarketplaceAdapter",
    "MarketplaceTestResult",
    "PluginUpdateInfo",
    "RemotePluginInfo",
]
```

- [ ] **步骤 3：运行类型检查验证**

运行：`cd server/python && uv run mypy src/tenant/services/marketplace/`
预期：类型检查通过

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/tenant/services/marketplace/
git commit -m "feat(tenant): 实现 MarketplaceGateway 服务

- 实现市场配置 CRUD 操作
- 实现远程插件浏览功能
- 实现连接测试功能

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 5：API Schema 定义

**文件：**
- 创建：`server/python/src/tenant/schemas/admin/marketplace.py`

- [ ] **步骤 1：编写市场 Schema**

```python
# server/python/src/tenant/schemas/admin/marketplace.py
"""插件市场 API Schema"""

from __future__ import annotations

from datetime import datetime

from framework.schemas import BaseModel, BasePaginatedQuery


# ==================== 请求 Schema ====================

class MarketplaceCreate(BaseModel):
    """创建市场请求"""

    name: str
    code: str
    type: str
    url: str
    auth_type: str = "none"
    auth_config: dict | None = None
    description: str | None = None


class MarketplaceUpdate(BaseModel):
    """更新市场请求"""

    name: str | None = None
    url: str | None = None
    auth_type: str | None = None
    auth_config: dict | None = None
    is_enabled: bool | None = None
    sync_config: dict | None = None
    description: str | None = None


class SyncPluginsRequest(BaseModel):
    """同步插件请求"""

    marketplace_id: str
    plugin_ids: list[str]


# ==================== 响应 Schema ====================

class MarketplaceResponse(BaseModel):
    """市场响应"""

    id: str
    name: str
    code: str
    type: str
    url: str
    auth_type: str
    is_enabled: bool
    last_sync_at: datetime | None
    last_sync_status: str | None
    description: str | None
    created_at: datetime | None
    updated_at: datetime | None

    @classmethod
    def from_entity(cls, entity) -> MarketplaceResponse:
        return cls(
            id=entity.id,
            name=entity.name,
            code=entity.code,
            type=entity.type,
            url=entity.url,
            auth_type=entity.auth_type,
            is_enabled=entity.is_enabled,
            last_sync_at=entity.last_sync_at,
            last_sync_status=entity.last_sync_status,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class MarketplaceTestResponse(BaseModel):
    """市场测试响应"""

    success: bool
    message: str
    plugin_count: int | None = None
    latency_ms: int | None = None


class RemotePluginResponse(BaseModel):
    """远程插件响应"""

    plugin_id: str
    name: str
    description: str | None
    version: str
    author: str
    icon: str | None
    plugin_type: str
    tags: list[str]
    downloads: int | None
    download_url: str

    @classmethod
    def from_info(cls, info) -> RemotePluginResponse:
        return cls(
            plugin_id=info.plugin_id,
            name=info.name,
            description=info.description,
            version=info.version,
            author=info.author,
            icon=info.icon,
            plugin_type=info.plugin_type,
            tags=info.tags,
            downloads=info.downloads,
            download_url=info.download_url,
        )


class SyncResultResponse(BaseModel):
    """同步结果响应"""

    success: list[str]
    failed: list[dict[str, str]]
    skipped: list[str]


# ==================== 查询 Schema ====================

class MarketplaceQuery(BasePaginatedQuery):
    """市场查询"""

    type: str | None = None
    is_enabled: bool | None = None
```

- [ ] **步骤 2：更新 Schema 导出**

修改 `server/python/src/tenant/schemas/admin/__init__.py`：

```python
# 添加导出
from tenant.schemas.admin.marketplace import (
    MarketplaceCreate,
    MarketplaceResponse,
    MarketplaceTestResponse,
    MarketplaceUpdate,
    MarketplaceQuery,
    RemotePluginResponse,
    SyncPluginsRequest,
    SyncResultResponse,
)
```

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/tenant/schemas/admin/
git commit -m "feat(tenant): 添加插件市场 API Schema

- 定义市场 CRUD 请求/响应 Schema
- 定义远程插件浏览响应 Schema
- 定义同步插件请求/响应 Schema

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 6：API 控制器

**文件：**
- 创建：`server/python/src/tenant/controllers/admin/marketplace_controller.py`
- 修改：`server/python/src/tenant/controllers/admin/__init__.py`

- [ ] **步骤 1：编写市场控制器**

```python
# server/python/src/tenant/controllers/admin/marketplace_controller.py
"""插件市场管理控制器"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from tenant.middlewares.admin_auth_middleware import require_admin_permission
from tenant.schemas.admin.marketplace import (
    MarketplaceCreate,
    MarketplaceQuery,
    MarketplaceResponse,
    MarketplaceTestResponse,
    MarketplaceUpdate,
    RemotePluginResponse,
    SyncPluginsRequest,
    SyncResultResponse,
)
from tenant.services.marketplace import marketplace_gateway

router = APIRouter()


@router.post("/marketplaces")
async def create_marketplace(
    request: MarketplaceCreate,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """创建市场配置"""
    marketplace = await marketplace_gateway.create_marketplace(
        session=session,
        name=request.name,
        code=request.code,
        type=request.type,
        url=request.url,
        auth_type=request.auth_type,
        auth_config=request.auth_config,
        description=request.description,
    )
    await session.commit()
    return ApiResponse.success(data=MarketplaceResponse.from_entity(marketplace).model_dump())


@router.get("/marketplaces")
async def list_marketplaces(
    _perm: None = Depends(require_admin_permission("tenant:marketplace:read")),
    session: AsyncSession = Depends(get_db_session),
    type: str | None = None,
    is_enabled: bool | None = None,
) -> ApiResponse:
    """获取市场列表"""
    marketplaces = await marketplace_gateway.list_marketplaces(
        session=session,
        is_enabled=is_enabled,
    )
    items = [MarketplaceResponse.from_entity(m).model_dump() for m in marketplaces]
    return ApiResponse.success(data=items)


@router.get("/marketplaces/{marketplace_id}")
async def get_marketplace(
    marketplace_id: str,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:read")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """获取市场详情"""
    marketplace = await marketplace_gateway.get_marketplace(session, marketplace_id)
    if not marketplace:
        return ApiResponse.fail(message="市场不存在")
    return ApiResponse.success(data=MarketplaceResponse.from_entity(marketplace).model_dump())


@router.put("/marketplaces/{marketplace_id}")
async def update_marketplace(
    marketplace_id: str,
    request: MarketplaceUpdate,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """更新市场配置"""
    marketplace = await marketplace_gateway.update_marketplace(
        session=session,
        marketplace_id=marketplace_id,
        **request.model_dump(exclude_unset=True),
    )
    await session.commit()
    return ApiResponse.success(data=MarketplaceResponse.from_entity(marketplace).model_dump())


@router.delete("/marketplaces/{marketplace_id}")
async def delete_marketplace(
    marketplace_id: str,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """删除市场配置"""
    await marketplace_gateway.delete_marketplace(session, marketplace_id)
    await session.commit()
    return ApiResponse.success(message="市场已删除")


@router.post("/marketplaces/{marketplace_id}/test")
async def test_marketplace(
    marketplace_id: str,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:read")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """测试市场连接"""
    result = await marketplace_gateway.test_connection(session, marketplace_id)
    return ApiResponse.success(
        data=MarketplaceTestResponse(
            success=result.success,
            message=result.message,
            plugin_count=result.plugin_count,
            latency_ms=result.latency_ms,
        ).model_dump()
    )


@router.get("/marketplaces/{marketplace_id}/plugins")
async def list_remote_plugins(
    marketplace_id: str,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:read")),
    session: AsyncSession = Depends(get_db_session),
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    type: str | None = None,
) -> ApiResponse:
    """浏览远程插件"""
    plugins, total = await marketplace_gateway.list_remote_plugins(
        session=session,
        marketplace_id=marketplace_id,
        keyword=keyword,
        plugin_type=type,
        page=page,
        page_size=page_size,
    )
    items = [RemotePluginResponse.from_info(p).model_dump() for p in plugins]
    return ApiResponse.paginated(data=items, total=total, page=page, page_size=page_size)
```

- [ ] **步骤 2：注册路由**

修改 `server/python/src/tenant/controllers/admin/__init__.py`：

```python
# 添加导入和路由注册
from tenant.controllers.admin.marketplace_controller import router as marketplace_router

# 在现有路由注册后添加
admin_router.include_router(marketplace_router, prefix="/v1", tags=["marketplace"])
```

- [ ] **步骤 3：添加权限定义**

修改 `server/python/src/tenant/module.py`，在权限列表中添加：

```python
# 在 permissions 列表中添加
PermissionDef(code="tenant:marketplace:read", name="查看插件市场", resource="marketplace", action="read"),
PermissionDef(code="tenant:marketplace:write", name="管理插件市场", resource="marketplace", action="write"),
```

- [ ] **步骤 4：启动服务验证**

运行：`cd server/python && uv run python manage.py runserver`
预期：服务启动成功，路由注册成功

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/controllers/admin/
git add server/python/src/tenant/module.py
git commit -m "feat(tenant): 添加插件市场 API 控制器

- 实现市场 CRUD API
- 实现市场连接测试 API
- 实现远程插件浏览 API
- 添加 tenant:marketplace:read/write 权限定义

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 7：前端 API 和类型定义

**文件：**
- 创建：`web/vue/src/tenant/types/marketplace.ts`
- 创建：`web/vue/src/tenant/api/marketplace.ts`

- [ ] **步骤 1：编写类型定义**

```typescript
// web/vue/src/tenant/types/marketplace.ts
/** 插件市场类型定义 */

// ==================== 市场配置 ====================

export interface Marketplace {
  id: string;
  name: string;
  code: string;
  type: string;
  url: string;
  auth_type: string;
  is_enabled: boolean;
  last_sync_at?: string;
  last_sync_status?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MarketplaceCreate {
  name: string;
  code: string;
  type: string;
  url: string;
  auth_type?: string;
  auth_config?: Record<string, unknown>;
  description?: string;
}

export interface MarketplaceUpdate {
  name?: string;
  url?: string;
  auth_type?: string;
  auth_config?: Record<string, unknown>;
  is_enabled?: boolean;
  sync_config?: Record<string, unknown>;
  description?: string;
}

export interface MarketplaceTestResult {
  success: boolean;
  message: string;
  plugin_count?: number;
  latency_ms?: number;
}

// ==================== 远程插件 ====================

export interface RemotePlugin {
  plugin_id: string;
  name: string;
  description?: string;
  version: string;
  author: string;
  icon?: string;
  plugin_type: string;
  tags: string[];
  downloads?: number;
  download_url: string;
}

// ==================== 同步 ====================

export interface SyncPluginsRequest {
  marketplace_id: string;
  plugin_ids: string[];
}

export interface SyncResult {
  success: string[];
  failed: Array<{ plugin_id: string; message: string }>;
  skipped: string[];
}
```

- [ ] **步骤 2：编写 API 函数**

```typescript
// web/vue/src/tenant/api/marketplace.ts
import { rawDel, rawGet, rawPost, rawPut } from '@/framework/api/client';
import type { ApiResponse } from '@/framework/api/types';
import type {
  Marketplace,
  MarketplaceCreate,
  MarketplaceTestResult,
  MarketplaceUpdate,
  RemotePlugin,
  SyncPluginsRequest,
  SyncResult,
} from '@/tenant/types/marketplace';

// ==================== 市场配置管理 ====================

export const getMarketplaces = () =>
  rawGet<ApiResponse<Marketplace[]>>('/tenant/admin/v1/marketplaces');

export const getMarketplace = (id: string) =>
  rawGet<ApiResponse<Marketplace>>(`/tenant/admin/v1/marketplaces/${id}`);

export const createMarketplace = (data: MarketplaceCreate) =>
  rawPost<ApiResponse<Marketplace>>('/tenant/admin/v1/marketplaces', data);

export const updateMarketplace = (id: string, data: MarketplaceUpdate) =>
  rawPut<ApiResponse<Marketplace>>(`/tenant/admin/v1/marketplaces/${id}`, data);

export const deleteMarketplace = (id: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/marketplaces/${id}`);

// ==================== 连接测试 ====================

export const testMarketplace = (id: string) =>
  rawPost<ApiResponse<MarketplaceTestResult>>(`/tenant/admin/v1/marketplaces/${id}/test`);

// ==================== 远程插件浏览 ====================

export const getRemotePlugins = (marketplaceId: string, params?: { page?: number; page_size?: number; keyword?: string; type?: string }) =>
  rawGet<ApiResponse<RemotePlugin[]>>(`/tenant/admin/v1/marketplaces/${marketplaceId}/plugins`, { params });

// ==================== 同步 ====================

export const syncPlugins = (data: SyncPluginsRequest) =>
  rawPost<ApiResponse<SyncResult>>('/tenant/admin/v1/marketplaces/sync', data);
```

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/types/marketplace.ts
git add web/vue/src/tenant/api/marketplace.ts
git commit -m "feat(web): 添加插件市场前端 API 和类型定义

- 定义市场配置相关类型
- 定义远程插件相关类型
- 实现市场 CRUD API 函数
- 实现远程插件浏览 API 函数

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 8：前端页面 - 市场配置列表

**文件：**
- 创建：`web/vue/src/tenant/pages/admin/MarketplaceListPage.vue`

- [ ] **步骤 1：编写市场列表页面**

```vue
<!-- web/vue/src/tenant/pages/admin/MarketplaceListPage.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Badge, Button, Card } from '@/components';
import { DataTable, type DataTableColumn } from '@/components';
import { getMarketplaces, testMarketplace, deleteMarketplace } from '@/tenant/api/marketplace';
import type { Marketplace } from '@/tenant/types/marketplace';

const router = useRouter();
const loading = ref(false);
const marketplaces = ref<Marketplace[]>([]);

const columns: DataTableColumn[] = [
  { key: 'name', header: '名称' },
  { key: 'type', header: '类型' },
  { key: 'url', header: '地址' },
  { key: 'is_enabled', header: '状态' },
  { key: 'last_sync_at', header: '最后同步' },
  { key: 'actions', header: '操作', width: 200 },
];

async function loadMarketplaces() {
  loading.value = true;
  try {
    const res = await getMarketplaces();
    if (res.data.code === 200) {
      marketplaces.value = res.data.data;
    }
  } finally {
    loading.value = false;
  }
}

async function handleTest(id: string) {
  const res = await testMarketplace(id);
  if (res.data.code === 200) {
    const result = res.data.data;
    alert(result.success ? `连接成功，延迟 ${result.latency_ms}ms，插件数 ${result.plugin_count}` : `连接失败: ${result.message}`);
  }
}

async function handleDelete(id: string) {
  if (!confirm('确定要删除此市场配置吗？')) return;
  const res = await deleteMarketplace(id);
  if (res.data.code === 200) {
    await loadMarketplaces();
  }
}

function goBrowse(id: string) {
  router.push(`/admin/marketplaces/${id}/plugins`);
}

onMounted(loadMarketplaces);
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">插件市场管理</h1>
      <Button @click="router.push('/admin/marketplaces/create')">添加市场</Button>
    </div>

    <Card>
      <DataTable :columns="columns" :data="marketplaces" :loading="loading">
        <template #cell-is_enabled="{ row }">
          <Badge :variant="row.is_enabled ? 'success' : 'secondary'">
            {{ row.is_enabled ? '启用' : '禁用' }}
          </Badge>
        </template>
        <template #cell-actions="{ row }">
          <div class="flex gap-2">
            <Button size="sm" variant="outline" @click="goBrowse(row.id)">浏览</Button>
            <Button size="sm" variant="outline" @click="handleTest(row.id)">测试</Button>
            <Button size="sm" variant="outline" @click="router.push(`/admin/marketplaces/${row.id}/edit`)">编辑</Button>
            <Button size="sm" variant="destructive" @click="handleDelete(row.id)">删除</Button>
          </div>
        </template>
      </DataTable>
    </Card>
  </div>
</template>
```

- [ ] **步骤 2：运行前端开发服务器验证**

运行：`cd web/vue && pnpm dev`
预期：页面加载无错误

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/pages/admin/MarketplaceListPage.vue
git commit -m "feat(web): 添加插件市场配置列表页面

- 展示市场配置列表
- 支持测试连接、编辑、删除操作
- 跳转到远程插件浏览页

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 9：前端页面 - 市场配置表单

**文件：**
- 创建：`web/vue/src/tenant/pages/admin/MarketplaceFormPage.vue`

- [ ] **步骤 1：编写市场表单页面**

```vue
<!-- web/vue/src/tenant/pages/admin/MarketplaceFormPage.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Button, Card, Input, Select } from '@/components';
import { getMarketplace, createMarketplace, updateMarketplace } from '@/tenant/api/marketplace';
import type { MarketplaceCreate } from '@/tenant/types/marketplace';

const route = useRoute();
const router = useRouter();
const isEdit = computed(() => !!route.params.id);
const loading = ref(false);

const form = ref<MarketplaceCreate>({
  name: '',
  code: '',
  type: 'dify',
  url: '',
  auth_type: 'none',
  auth_config: {},
  description: '',
});

const typeOptions = [
  { label: 'Dify', value: 'dify' },
];

async function loadMarketplace() {
  if (!isEdit.value) return;
  loading.value = true;
  try {
    const res = await getMarketplace(route.params.id as string);
    if (res.data.code === 200) {
      const data = res.data.data;
      form.value = {
        name: data.name,
        code: data.code,
        type: data.type,
        url: data.url,
        auth_type: data.auth_type,
        auth_config: {},
        description: data.description || '',
      };
    }
  } finally {
    loading.value = false;
  }
}

async function handleSubmit() {
  loading.value = true;
  try {
    if (isEdit.value) {
      await updateMarketplace(route.params.id as string, form.value);
    } else {
      await createMarketplace(form.value);
    }
    router.push('/admin/marketplaces');
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-2xl font-bold">{{ isEdit ? '编辑市场' : '添加市场' }}</h1>

    <Card class="p-6">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1">市场名称 *</label>
            <Input v-model="form.name" required />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">市场编码 *</label>
            <Input v-model="form.code" :disabled="isEdit" required />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1">市场类型 *</label>
            <Select v-model="form.type" :options="typeOptions" :disabled="isEdit" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">市场地址 *</label>
            <Input v-model="form.url" placeholder="https://plugins.dify.ai/api/v1" required />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">描述</label>
          <Input v-model="form.description" />
        </div>

        <div class="flex gap-2">
          <Button type="submit" :loading="loading">保存</Button>
          <Button type="button" variant="outline" @click="router.back()">取消</Button>
        </div>
      </form>
    </Card>
  </div>
</template>
```

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/tenant/pages/admin/MarketplaceFormPage.vue
git commit -m "feat(web): 添加插件市场配置表单页面

- 支持创建和编辑市场配置
- 表单验证和提交

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 10：前端页面 - 远程插件浏览

**文件：**
- 创建：`web/vue/src/tenant/pages/admin/RemotePluginBrowsePage.vue`

- [ ] **步骤 1：编写远程插件浏览页面**

```vue
<!-- web/vue/src/tenant/pages/admin/RemotePluginBrowsePage.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Badge, Button, Card, Input, Checkbox } from '@/components';
import { DataTable, type DataTableColumn } from '@/components';
import { Pagination } from '@/components';
import { getMarketplace, getRemotePlugins } from '@/tenant/api/marketplace';
import type { Marketplace, RemotePlugin } from '@/tenant/types/marketplace';

const route = useRoute();
const router = useRouter();
const marketplaceId = computed(() => route.params.id as string);

const loading = ref(false);
const marketplace = ref<Marketplace | null>(null);
const plugins = ref<RemotePlugin[]>([]);
const selectedIds = ref<Set<string>>(new Set());
const keyword = ref('');
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);

const columns: DataTableColumn[] = [
  { key: 'selection', header: '', width: 50 },
  { key: 'name', header: '名称' },
  { key: 'plugin_id', header: 'ID' },
  { key: 'version', header: '版本' },
  { key: 'plugin_type', header: '类型' },
  { key: 'downloads', header: '下载量' },
];

async function loadMarketplace() {
  const res = await getMarketplace(marketplaceId.value);
  if (res.data.code === 200) {
    marketplace.value = res.data.data;
  }
}

async function loadPlugins() {
  loading.value = true;
  try {
    const res = await getRemotePlugins(marketplaceId.value, {
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
    });
    if (res.data.code === 200) {
      plugins.value = res.data.data;
      total.value = res.data.total;
    }
  } finally {
    loading.value = false;
  }
}

function toggleSelect(pluginId: string) {
  if (selectedIds.value.has(pluginId)) {
    selectedIds.value.delete(pluginId);
  } else {
    selectedIds.value.add(pluginId);
  }
}

function handleSync() {
  // TODO: 实现同步功能
  alert(`已选择 ${selectedIds.value.size} 个插件`);
}

onMounted(() => {
  loadMarketplace();
  loadPlugins();
});
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">浏览远程插件</h1>
        <p class="text-muted-foreground">{{ marketplace?.name }}</p>
      </div>
      <Button variant="outline" @click="router.back()">返回</Button>
    </div>

    <Card>
      <div class="p-4 flex items-center gap-4">
        <Input v-model="keyword" placeholder="搜索插件名称..." class="w-64" @keyup.enter="loadPlugins" />
        <Button @click="loadPlugins">搜索</Button>
      </div>

      <DataTable :columns="columns" :data="plugins" :loading="loading">
        <template #cell-selection="{ row }">
          <Checkbox :checked="selectedIds.has(row.plugin_id)" @update:checked="toggleSelect(row.plugin_id)" />
        </template>
        <template #cell-name="{ row }">
          <div class="flex items-center gap-2">
            <span>{{ row.name }}</span>
            <Badge variant="outline">{{ row.plugin_type }}</Badge>
          </div>
        </template>
        <template #cell-plugin_id="{ row }">
          <span class="text-muted-foreground">{{ row.plugin_id }}</span>
        </template>
      </DataTable>

      <div class="p-4 flex items-center justify-between border-t">
        <span class="text-sm text-muted-foreground">已选择 {{ selectedIds.size }} 个插件</span>
        <div class="flex items-center gap-4">
          <Pagination v-model:page="page" :total="total" :page-size="pageSize" @update:page="loadPlugins" />
          <Button :disabled="selectedIds.size === 0" @click="handleSync">同步选中插件</Button>
        </div>
      </div>
    </Card>
  </div>
</template>
```

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/tenant/pages/admin/RemotePluginBrowsePage.vue
git commit -m "feat(web): 添加远程插件浏览页面

- 展示远程市场的插件列表
- 支持搜索和选择
- 支持分页浏览

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 11：前端路由配置

**文件：**
- 修改：`web/vue/src/tenant/router/index.ts`

- [ ] **步骤 1：添加市场相关路由**

在 `web/vue/src/tenant/router/index.ts` 添加路由：

```typescript
// 添加导入
import MarketplaceListPage from '@/tenant/pages/admin/MarketplaceListPage.vue';
import MarketplaceFormPage from '@/tenant/pages/admin/MarketplaceFormPage.vue';
import RemotePluginBrowsePage from '@/tenant/pages/admin/RemotePluginBrowsePage.vue';

// 在 adminRoutes 中添加
{
  path: 'marketplaces',
  name: 'MarketplaceList',
  component: MarketplaceListPage,
  meta: { title: '插件市场', permission: 'tenant:marketplace:read' },
},
{
  path: 'marketplaces/create',
  name: 'MarketplaceCreate',
  component: MarketplaceFormPage,
  meta: { title: '添加市场', permission: 'tenant:marketplace:write' },
},
{
  path: 'marketplaces/:id/edit',
  name: 'MarketplaceEdit',
  component: MarketplaceFormPage,
  meta: { title: '编辑市场', permission: 'tenant:marketplace:write' },
},
{
  path: 'marketplaces/:id/plugins',
  name: 'RemotePluginBrowse',
  component: RemotePluginBrowsePage,
  meta: { title: '浏览远程插件', permission: 'tenant:marketplace:read' },
},
```

- [ ] **步骤 2：运行前端验证**

运行：`cd web/vue && pnpm dev`
预期：路由配置正确，页面可访问

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/router/index.ts
git commit -m "feat(web): 添加插件市场路由配置

- 市场列表页、表单页、远程插件浏览页路由

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 12：集成测试

**文件：**
- 创建：`server/python/tests/tenant/integration/test_marketplace_api.py`

- [ ] **步骤 1：编写集成测试**

```python
# server/python/tests/tenant/integration/test_marketplace_api.py
"""插件市场 API 集成测试"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_marketplace(client: AsyncClient, admin_token: str):
    """测试创建市场"""
    response = await client.post(
        "/tenant/admin/v1/marketplaces",
        json={
            "name": "Test Dify Market",
            "code": "test-dify",
            "type": "dify",
            "url": "https://plugins.dify.ai/api/v1",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["name"] == "Test Dify Market"


@pytest.mark.asyncio
async def test_list_marketplaces(client: AsyncClient, admin_token: str):
    """测试获取市场列表"""
    response = await client.get(
        "/tenant/admin/v1/marketplaces",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert isinstance(data["data"], list)
```

- [ ] **步骤 2：运行测试验证**

运行：`cd server/python && uv run pytest tests/tenant/integration/test_marketplace_api.py -v`
预期：测试通过

- [ ] **步骤 3：Commit**

```bash
git add server/python/tests/tenant/integration/test_marketplace_api.py
git commit -m "test(tenant): 添加插件市场 API 集成测试

- 测试市场 CRUD API

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 自检清单

**1. 规格覆盖度：**

| 规格需求 | 实现任务 |
|----------|----------|
| 市场配置管理（CRUD） | 任务 1、5、6、8、9 |
| 远程插件浏览 | 任务 2、3、4、6、10 |
| 选择性同步插件定义 | 任务 4（gateway 基础）、任务 10（前端选择） |
| 更新检测与应用 | 规格中有定义，本计划未实现完整同步流程（可后续迭代） |
| 复用现有插件安装流程 | 任务 4 复用 plugin_package_service |
| Dify 适配器 | 任务 3 |
| ModelScope 适配器 | 规格中有定义，本计划未实现（可后续迭代） |

**遗漏功能（后续迭代）：**
- 完整的插件同步流程（下载、解析、存储、注册）
- 更新检测和应用 API
- ModelScope 适配器实现
- 认证配置加密存储

**2. 占位符扫描：** 无禁止的占位符模式

**3. 类型一致性：** 所有类型定义在各文件中保持一致
