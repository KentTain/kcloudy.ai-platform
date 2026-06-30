# 插件同步与 ModelScope 适配器实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现完整的插件同步流程和 ModelScope 适配器，支持从远程市场同步插件定义，支持更新检测和应用。

**架构：** 在现有 MarketplaceGateway 上扩展同步方法，新增 ModelScopeAdapter 实现适配器协议。同步流程复用 plugin_package_service（解析）、plugin_storage_service（存储）和 plugin_definition_service（注册）。

**技术栈：** Python 3.12 + FastAPI + SQLAlchemy 2.0 + httpx + modelscope SDK（后端），Vue 3 + TypeScript（前端）

---

## 文件结构

### 新增文件

| 文件 | 职责 |
|------|------|
| `server/python/src/tenant/services/marketplace/adapters/modelscope_adapter.py` | ModelScope 适配器实现 |
| `server/python/tests/tenant/unit/services/marketplace/test_modelscope_adapter.py` | ModelScope 适配器单元测试 |
| `server/python/tests/tenant/integration/test_marketplace_sync_api.py` | 同步 API 集成测试 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `server/python/src/tenant/services/marketplace/gateway.py` | 添加 sync_plugins、check_updates、apply_update 方法 |
| `server/python/src/tenant/services/marketplace/adapters/__init__.py` | 添加 ModelScopeAdapter 导出 |
| `server/python/src/tenant/services/marketplace/__init__.py` | 添加 ModelScopeAdapter 导出 |
| `server/python/src/tenant/schemas/admin/marketplace.py` | 添加 SyncPluginItem、SyncResult、PluginUpdateResponse 等 Schema |
| `server/python/src/tenant/controllers/admin/marketplace_controller.py` | 添加同步、检查更新、应用更新端点 |
| `web/vue/src/tenant/types/marketplace.ts` | 修改 SyncPluginsRequest 类型 |
| `web/vue/src/tenant/api/marketplace.ts` | 添加同步、更新 API 函数 |
| `web/vue/src/tenant/pages/admin/RemotePluginBrowsePage.vue` | 添加类型选择和同步进度 |
| `web/vue/src/tenant/pages/admin/MarketplaceListPage.vue` | 添加检查更新按钮 |

---

## 任务 1：ModelScope 适配器实现

**文件：**
- 创建：`server/python/src/tenant/services/marketplace/adapters/modelscope_adapter.py`
- 创建：`server/python/tests/tenant/unit/services/marketplace/test_modelscope_adapter.py`
- 修改：`server/python/src/tenant/services/marketplace/adapters/__init__.py`
- 修改：`server/python/src/tenant/services/marketplace/__init__.py`

### 步骤 1：编写 ModelScope 适配器

```python
# server/python/src/tenant/services/marketplace/adapters/modelscope_adapter.py
"""ModelScope 模型市场适配器"""

from __future__ import annotations

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
                    f"{self.API_BASE}/models", headers=headers, params={"Page": 1, "PageSize": 1}
                )
                latency_ms = int((time.time() - start_time) * 1000)
                if response.status_code == 200:
                    data = response.json()
                    total = data.get("Data", {}).get("TotalCount", 0)
                    return MarketplaceTestResult(success=True, message="连接成功", plugin_count=total, latency_ms=latency_ms)
                return MarketplaceTestResult(success=False, message=f"连接失败: HTTP {response.status_code}", latency_ms=latency_ms)
        except httpx.TimeoutException:
            return MarketplaceTestResult(success=False, message="连接超时")
        except Exception as e:
            logger.error(f"测试 ModelScope 市场连接失败: {e}")
            return MarketplaceTestResult(success=False, message=f"连接异常: {str(e)}")

    async def list_plugins(self, config: dict, keyword: str | None = None, plugin_type: str | None = None, page: int = 1, page_size: int = 20) -> tuple[Sequence[RemotePluginInfo], int]:
        headers = self._build_headers(config)
        params: dict[str, Any] = {"Page": page, "PageSize": page_size}
        if keyword:
            params["Name"] = keyword
        if plugin_type:
            params["Task"] = plugin_type
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.API_BASE}/models", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        plugins = [self._parse_model(item) for item in data.get("Data", {}).get("Models", [])]
        return plugins, data.get("Data", {}).get("TotalCount", 0)

    async def get_plugin(self, config: dict, plugin_id: str) -> RemotePluginInfo | None:
        headers = self._build_headers(config)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.API_BASE}/models/{plugin_id}", headers=headers)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return self._parse_model(response.json().get("Data", {}))
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def download_plugin(self, config: dict, plugin_id: str, version: str | None = None) -> tuple[bytes, str]:
        from modelscope import snapshot_download
        auth_config = config.get("auth_config", {})
        api_token = auth_config.get("api_token", "")
        with tempfile.TemporaryDirectory() as temp_dir:
            local_dir = snapshot_download(model_id=plugin_id, revision=version or "master", api_token=api_token, cache_dir=temp_dir)
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
                    for file in files:
                        zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), local_dir))
                zf.writestr("manifest.yaml", yaml.dump(manifest))
            with open(zip_path, "rb") as f:
                zip_data = f.read()
        checksum = hashlib.sha256(zip_data).hexdigest()
        return zip_data, checksum

    async def check_updates(self, config: dict, plugins: Sequence[dict]) -> Sequence[PluginUpdateInfo]:
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
                    results.append(PluginUpdateInfo(plugin_id=plugin_id, current_version=current_version or "", latest_version=remote.version, has_update=has_update, changelog=None))
            except Exception as e:
                logger.warning(f"检查插件更新失败: {plugin_id}, 错误: {e}")
        return results

    def _parse_model(self, item: dict) -> RemotePluginInfo:
        namespace = item.get("Namespace", "")
        name = item.get("Name", "")
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
            download_url=f"modelscope://{plugin_id}",
            created_at=self._parse_datetime(item.get("CreateTime")),
            updated_at=self._parse_datetime(item.get("UpdateTime")),
        )

    def _parse_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
```

### 步骤 2：编写适配器单元测试

```python
# server/python/tests/tenant/unit/services/marketplace/test_modelscope_adapter.py
"""ModelScope 适配器单元测试"""

import pytest
from datetime import datetime
from tenant.services.marketplace.adapters.modelscope_adapter import ModelScopeAdapter


@pytest.fixture
def adapter():
    return ModelScopeAdapter()


@pytest.mark.asyncio
async def test_market_type(adapter: ModelScopeAdapter):
    assert adapter.market_type == "modelscope"


@pytest.mark.asyncio
async def test_build_headers_with_token(adapter: ModelScopeAdapter):
    config = {"auth_config": {"api_token": "test-token"}}
    headers = adapter._build_headers(config)
    assert headers["Authorization"] == "Bearer test-token"


@pytest.mark.asyncio
async def test_build_headers_no_token(adapter: ModelScopeAdapter):
    config = {"auth_config": {}}
    headers = adapter._build_headers(config)
    assert "Authorization" not in headers


@pytest.mark.asyncio
async def test_parse_datetime_valid(adapter: ModelScopeAdapter):
    result = adapter._parse_datetime("2026-01-15T10:30:00Z")
    assert isinstance(result, datetime)
    assert result.year == 2026


@pytest.mark.asyncio
async def test_parse_datetime_none(adapter: ModelScopeAdapter):
    assert adapter._parse_datetime(None) is None


@pytest.mark.asyncio
async def test_parse_model(adapter: ModelScopeAdapter):
    data = {"Namespace": "Qwen", "Name": "Qwen2.5-72B", "ChineseName": "通义千问", "Description": "A large model", "Version": "1.0.0", "Tags": ["chat", "nlp"], "Downloads": 10000, "CreateTime": "2026-01-15T10:30:00Z", "UpdateTime": "2026-06-01T08:00:00Z"}
    plugin = adapter._parse_model(data)
    assert plugin.plugin_id == "Qwen/Qwen2.5-72B"
    assert plugin.name == "通义千问"
    assert plugin.author == "Qwen"
    assert plugin.version == "1.0.0"
    assert "chat" in plugin.tags
    assert plugin.downloads == 10000
```

### 步骤 3：运行测试

运行：`cd server/python && uv run pytest tests/tenant/unit/services/marketplace/test_modelscope_adapter.py -v`
预期：所有测试 PASS

### 步骤 4：更新适配器导出

修改 `server/python/src/tenant/services/marketplace/adapters/__init__.py`：

```python
from tenant.services.marketplace.adapters.dify_adapter import DifyAdapter
from tenant.services.marketplace.adapters.modelscope_adapter import ModelScopeAdapter

__all__ = ["DifyAdapter", "ModelScopeAdapter"]
```

### 步骤 5：Commit

```bash
git add server/python/src/tenant/services/marketplace/adapters/
git add server/python/tests/tenant/unit/services/marketplace/
git commit -m "feat(tenant): 实现 ModelScope 市场适配器"
```

---

## 任务 2：Gateway 同步方法

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/gateway.py`

### 步骤 1：添加同步方法

在 `MarketplaceGateway` 类中添加以下方法：

```python
async def sync_plugins(
    self,
    session: AsyncSession,
    marketplace_id: str,
    plugins: list[dict[str, str]],
) -> dict[str, Any]:
    """同步选中插件"""
    from tenant.services.plugin_package_service import plugin_package_service
    from tenant.services.plugin_storage_service import plugin_storage_service
    from tenant.models import TenantPluginDefinition

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

            # 2. 检查本地是否已存在
            existing = await session.execute(
                select(TenantPluginDefinition).where(
                    TenantPluginDefinition.plugin_id == plugin_id
                )
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
```

### 步骤 2：添加更新检查方法

```python
async def check_updates(
    self,
    session: AsyncSession,
    marketplace_id: str,
) -> Sequence[PluginUpdateInfo]:
    """检查插件更新"""
    from tenant.models import TenantPluginDefinition

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
```

### 步骤 3：添加应用更新方法

```python
async def apply_update(
    self,
    session: AsyncSession,
    marketplace_id: str,
    plugin_id: str,
) -> dict[str, Any]:
    """应用插件更新"""
    from tenant.models import TenantPluginDefinition

    marketplace = await self.get_marketplace(session, marketplace_id)
    if not marketplace:
        raise ValueError(f"市场不存在: {marketplace_id}")

    # 获取本地插件定义
    result = await session.execute(
        select(TenantPluginDefinition).where(
            TenantPluginDefinition.plugin_id == plugin_id,
            TenantPluginDefinition.source_type == "remote",
        )
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
```

### 步骤 4：运行测试验证

运行：`cd server/python && uv run pytest tests/tenant/unit/ -v`
预期：所有测试通过

### 步骤 5：Commit

```bash
git add server/python/src/tenant/services/marketplace/gateway.py
git commit -m "feat(tenant): 添加插件同步和更新功能"
```

---

## 任务 3：API Schema 扩展

**文件：**
- 修改：`server/python/src/tenant/schemas/admin/marketplace.py`

### 步骤 1：添加同步和更新 Schema

```python
# ==================== 同步 Schema ====================

class SyncPluginItem(BaseModel):
    """单个同步插件项"""
    plugin_id: str
    plugin_type: str = "tool"


class SyncPluginsRequest(BaseModel):
    """同步插件请求"""
    marketplace_id: str
    plugins: list[SyncPluginItem]


class SyncSuccessItem(BaseModel):
    """同步成功项"""
    plugin_id: str
    version: str


class SyncFailedItem(BaseModel):
    """同步失败项"""
    plugin_id: str
    message: str


class SyncSkippedItem(BaseModel):
    """跳过项"""
    plugin_id: str
    reason: str


class SyncResultResponse(BaseModel):
    """同步结果响应"""
    success: list[SyncSuccessItem] = []
    failed: list[SyncFailedItem] = []
    skipped: list[SyncSkippedItem] = []


# ==================== 更新 Schema ====================

class PluginUpdateResponse(BaseModel):
    """插件更新响应"""
    plugin_id: str
    current_version: str
    latest_version: str
    has_update: bool


class ApplyUpdateRequest(BaseModel):
    """应用更新请求"""
    marketplace_id: str


class ApplyUpdateResult(BaseModel):
    """应用更新结果"""
    plugin_id: str
    old_version: str
    new_version: str
    status: str
```

### 步骤 2：更新导出

修改 `server/python/src/tenant/schemas/admin/__init__.py` 添加新 Schema。

### 步骤 3：运行类型检查

运行：`cd server/python && uv run mypy src/tenant/schemas/admin/marketplace.py`
预期：类型检查通过

### 步骤 4：Commit

```bash
git add server/python/src/tenant/schemas/admin/marketplace.py
git commit -m "feat(tenant): 添加同步和更新相关 Schema"
```

---

## 任务 4：API 控制器扩展

**文件：**
- 修改：`server/python/src/tenant/controllers/admin/marketplace_controller.py`

### 步骤 1：添加同步端点

```python
@router.post("/marketplaces/sync")
async def sync_plugins(
    request: SyncPluginsRequest,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """同步选中插件"""
    try:
        result = await marketplace_gateway.sync_plugins(
            session=session,
            marketplace_id=request.marketplace_id,
            plugins=[p.model_dump() for p in request.plugins],
        )
        await session.commit()
        return ApiResponse.success(data=SyncResultResponse(**result).model_dump())
    except ValueError as e:
        return ApiResponse.fail(message=str(e))
```

### 步骤 2：添加更新检查端点

```python
@router.get("/marketplaces/updates")
async def check_updates(
    marketplace_id: str,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:read")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """检查插件更新"""
    try:
        updates = await marketplace_gateway.check_updates(
            session=session, marketplace_id=marketplace_id
        )
        items = [PluginUpdateResponse(
            plugin_id=u.plugin_id,
            current_version=u.current_version,
            latest_version=u.latest_version,
            has_update=u.has_update,
        ).model_dump() for u in updates]
        return ApiResponse.success(data=items)
    except ValueError as e:
        return ApiResponse.fail(message=str(e))
```

### 步骤 3：添加应用更新端点

```python
@router.post("/marketplaces/updates/{plugin_id}")
async def apply_update(
    plugin_id: str,
    request: ApplyUpdateRequest,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """应用插件更新"""
    try:
        result = await marketplace_gateway.apply_update(
            session=session,
            marketplace_id=request.marketplace_id,
            plugin_id=plugin_id,
        )
        await session.commit()
        return ApiResponse.success(data=ApplyUpdateResult(**result).model_dump())
    except ValueError as e:
        return ApiResponse.fail(message=str(e))
```

### 步骤 4：启动服务验证

运行：`cd server/python && uv run python manage.py runserver`
预期：服务启动成功，新路由注册成功

### 步骤 5：Commit

```bash
git add server/python/src/tenant/controllers/admin/marketplace_controller.py
git commit -m "feat(tenant): 添加同步和更新 API 端点"
```

---

## 任务 5：前端类型和 API

**文件：**
- 修改：`web/vue/src/tenant/types/marketplace.ts`
- 修改：`web/vue/src/tenant/api/marketplace.ts`

### 步骤 1：修改类型定义

```typescript
// web/vue/src/tenant/types/marketplace.ts

// 修改同步请求类型
export interface SyncPluginItem {
  plugin_id: string;
  plugin_type: string;
}

export interface SyncPluginsRequest {
  marketplace_id: string;
  plugins: SyncPluginItem[];
}

// 新增同步结果类型
export interface SyncSuccessItem {
  plugin_id: string;
  version: string;
}

export interface SyncFailedItem {
  plugin_id: string;
  message: string;
}

export interface SyncSkippedItem {
  plugin_id: string;
  reason: string;
}

export interface SyncResultResponse {
  success: SyncSuccessItem[];
  failed: SyncFailedItem[];
  skipped: SyncSkippedItem[];
}

// 新增更新类型
export interface PluginUpdateInfo {
  plugin_id: string;
  current_version: string;
  latest_version: string;
  has_update: boolean;
}

export interface ApplyUpdateResult {
  plugin_id: string;
  old_version: string;
  new_version: string;
  status: string;
}
```

### 步骤 2：添加 API 函数

```typescript
// web/vue/src/tenant/api/marketplace.ts

// 同步插件
export const syncPlugins = (data: SyncPluginsRequest) =>
  rawPost<ApiResponse<SyncResultResponse>>('/tenant/admin/v1/marketplaces/sync', data);

// 检查更新
export const checkUpdates = (marketplaceId: string) =>
  rawGet<ApiResponse<PluginUpdateInfo[]>>('/tenant/admin/v1/marketplaces/updates', {
    params: { marketplace_id: marketplaceId },
  });

// 应用更新
export const applyPluginUpdate = (pluginId: string, marketplaceId: string) =>
  rawPost<ApiResponse<ApplyUpdateResult>>(`/tenant/admin/v1/marketplaces/updates/${pluginId}`, {
    marketplace_id: marketplaceId,
  });
```

### 步骤 3：Commit

```bash
git add web/vue/src/tenant/types/marketplace.ts
git add web/vue/src/tenant/api/marketplace.ts
git commit -m "feat(web): 添加同步和更新前端类型与 API"
```

---

## 任务 6：前端页面修改

**文件：**
- 修改：`web/vue/src/tenant/pages/admin/RemotePluginBrowsePage.vue`
- 修改：`web/vue/src/tenant/pages/admin/MarketplaceListPage.vue`

### 步骤 1：修改 RemotePluginBrowsePage

主要修改内容：
1. 修改选择逻辑：选中时需记录 plugin_type
2. 修改同步按钮：调用新的 syncPlugins API
3. 添加同步进度弹窗

```typescript
// 修改选择逻辑
const selectedItems = ref<Map<string, string>>(new Map()); // plugin_id -> plugin_type

function toggleSelect(pluginId: string, pluginType: string) {
  if (selectedItems.value.has(pluginId)) {
    selectedItems.value.delete(pluginId);
  } else {
    selectedItems.value.set(pluginId, pluginType);
  }
}

// 修改同步逻辑
async function handleSync() {
  if (selectedItems.value.size === 0) return;

  const plugins = Array.from(selectedItems.value.entries()).map(([plugin_id, plugin_type]) => ({
    plugin_id,
    plugin_type,
  }));

  try {
    const res = await syncPlugins({
      marketplace_id: marketplaceId.value,
      plugins,
    });

    if (res.data.code === 200) {
      const result = res.data.data;
      alert(`同步完成: 成功 ${result.success.length} 个, 失败 ${result.failed.length} 个, 跳过 ${result.skipped.length} 个`);
      selectedItems.value.clear();
      await loadPlugins();
    }
  } catch (error) {
    alert("同步失败");
  }
}
```

### 步骤 2：修改 MarketplaceListPage 添加"检查更新"按钮

在操作列添加"检查更新"按钮，点击后调用 checkUpdates API 并弹出更新列表。

### 步骤 3：验证前端构建

运行：`cd web/vue && pnpm check`
预期：类型检查通过，无错误

### 步骤 4：Commit

```bash
git add web/vue/src/tenant/pages/admin/
git commit -m "feat(web): 添加插件同步和更新前端功能"
```

---

## 任务 7：集成测试

**文件：**
- 创建：`server/python/tests/tenant/integration/test_marketplace_sync_api.py`

### 步骤 1：编写集成测试

```python
"""插件市场同步 API 集成测试"""

import pytest


@pytest.mark.asyncio
async def test_sync_plugins(client, admin_token, test_marketplace):
    """测试同步插件"""
    response = await client.post(
        "/tenant/admin/v1/marketplaces/sync",
        json={
            "marketplace_id": test_marketplace,
            "plugins": [{"plugin_id": "test/plugin", "plugin_type": "tool"}],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200


@pytest.mark.asyncio
async def test_check_updates(client, admin_token, test_marketplace):
    """测试检查更新"""
    response = await client.get(
        "/tenant/admin/v1/marketplaces/updates",
        params={"marketplace_id": test_marketplace},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_apply_update(client, admin_token, test_marketplace):
    """测试应用更新"""
    response = await client.post(
        f"/tenant/admin/v1/marketplaces/updates/test-plugin",
        json={"marketplace_id": test_marketplace},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
```

### 步骤 2：运行测试

运行：`cd server/python && uv run pytest tests/tenant/integration/test_marketplace_sync_api.py -v`
预期：测试通过

### 步骤 3：Commit

```bash
git add server/python/tests/tenant/integration/test_marketplace_sync_api.py
git commit -m "test(tenant): 添加插件同步 API 集成测试"
```
