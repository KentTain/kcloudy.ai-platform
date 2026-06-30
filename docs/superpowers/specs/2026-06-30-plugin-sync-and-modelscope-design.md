# 插件同步与 ModelScope 适配器设计规格

## 1. 概述

### 1.1 背景

远程插件市场功能已完成基础实现，包括市场配置管理、远程插件浏览、Dify 适配器。现需要补充完整的插件同步流程和 ModelScope 适配器实现。

### 1.2 目标

- 实现完整的插件同步流程（下载、解析、存储、注册）
- 实现 ModelScope 适配器，支持从 ModelScope 获取模型插件
- 支持插件更新检测和应用
- 复用现有插件包解析和存储服务

### 1.3 范围

| 包含 | 不包含 |
|------|--------|
| 手动选择同步 | 定时自动同步 |
| 覆盖更新策略 | 多版本并存 |
| 部分成功处理 | 全量回滚 |
| ModelScope SDK 下载 | Git 克隆下载 |
| API Token 认证 | OAuth 认证 |

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      插件同步与 ModelScope 扩展架构                           │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   前端页面       │
                              │  远程插件浏览页  │
                              └────────┬────────┘
                                       │ 选择插件 + 指定类型
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  API 层                                                                      │
│  POST /tenant/admin/v1/marketplaces/sync         同步插件                  │
│  GET  /tenant/admin/v1/marketplaces/updates      检查更新                  │
│  POST /tenant/admin/v1/marketplaces/updates/{id} 应用更新                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  MarketplaceGateway（扩展）                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  sync_plugins()           - 协调同步流程                             │   │
│  │  check_updates()          - 检查插件更新                             │   │
│  │  apply_update()           - 应用单个插件更新                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                          │                                                  │
│         ┌────────────────┴────────────────┐                                │
│         ▼                                 ▼                                │
│  ┌─────────────────┐             ┌─────────────────┐                       │
│  │  DifyAdapter    │             │ModelScopeAdapter│  ← 新增               │
│  │  (已实现)       │             │                 │                       │
│  └─────────────────┘             └─────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  复用服务                                                                     │
│  plugin_package_service     解析插件包                                       │
│  plugin_storage_service     存储 MinIO                                       │
│  plugin_definition_service  注册插件定义                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 核心组件

| 组件 | 职责 | 位置 |
|------|------|------|
| MarketplaceGateway | 扩展同步、更新检查、应用更新方法 | `tenant/services/marketplace/gateway.py` |
| ModelScopeAdapter | ModelScope 市场适配器实现 | `tenant/services/marketplace/adapters/modelscope_adapter.py` |

---

## 3. 插件同步流程

### 3.1 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                     插件同步流程                                 │
└─────────────────────────────────────────────────────────────────┘

用户选择插件 + 指定类型
        │
        ▼
┌───────────────────────────────────────────┐
│  1. 获取远程插件信息                        │
│     adapter.get_plugin(config, plugin_id) │
└───────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────┐
│  2. 检查本地是否已存在相同版本              │
│     query plugin_definitions by plugin_id │
│     ┌─────────────────────────────────┐   │
│     │ 相同版本已存在 → 跳过           │   │
│     │ 不同版本存在 → 覆盖更新         │   │
│     │ 不存在 → 新增                   │   │
│     └─────────────────────────────────┘   │
└───────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────┐
│  3. 下载插件包                              │
│     adapter.download_plugin()             │
│     返回: (bytes, checksum)               │
└───────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────┐
│  4. 解析验证                                │
│     plugin_package_service.parse()        │
│     返回: PluginPackageInfo                │
└───────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────┐
│  5. 存储到 MinIO                            │
│     plugin_storage_service.upload()       │
│     返回: storage_path                     │
└───────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────┐
│  6. 创建/更新 plugin_definitions 记录       │
│     source_type = "remote"                 │
│     marketplace_id = 来源市场ID            │
│     remote_version = 远程版本              │
│     local_version = 本地版本               │
└───────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────┐
│  7. 记录同步结果                            │
│     success: [plugin_id, ...]             │
│     failed: [{plugin_id, error}, ...]     │
│     skipped: [plugin_id, ...]             │
└───────────────────────────────────────────┘
```

### 3.2 同步策略

| 场景 | 策略 |
|------|------|
| 相同版本已存在 | 跳过，添加到 skipped 列表 |
| 不同版本存在 | 覆盖更新，更新 plugin_definitions 记录 |
| 不存在 | 新增 plugin_definitions 记录 |
| 单个插件失败 | 记录到 failed 列表，继续处理其他插件 |

### 3.3 Gateway 方法签名

```python
async def sync_plugins(
    self,
    session: AsyncSession,
    marketplace_id: str,
    plugins: list[dict[str, str]],  # [{"plugin_id": "xxx", "plugin_type": "model"}]
) -> SyncResult:
    """同步选中的插件
    
    Args:
        session: 数据库会话
        marketplace_id: 市场ID
        plugins: 要同步的插件列表，每项包含 plugin_id 和 plugin_type
    
    Returns:
        SyncResult: 包含 success、failed、skipped 列表
    """
    ...

async def check_updates(
    self,
    session: AsyncSession,
    marketplace_id: str,
) -> list[PluginUpdateInfo]:
    """检查市场插件的更新
    
    Args:
        session: 数据库会话
        marketplace_id: 市场ID
    
    Returns:
        list[PluginUpdateInfo]: 有更新的插件列表
    """
    ...

async def apply_update(
    self,
    session: AsyncSession,
    marketplace_id: str,
    plugin_id: str,
) -> dict[str, Any]:
    """应用单个插件的更新
    
    Args:
        session: 数据库会话
        marketplace_id: 市场ID
        plugin_id: 插件ID
    
    Returns:
        dict: 更新结果，包含新旧版本信息
    """
    ...
```

---

## 4. ModelScope 适配器

### 4.1 API 映射

| MarketplaceAdapter 方法 | ModelScope API | 说明 |
|------------------------|----------------|------|
| `test_connection` | `GET /api/v1/models` | 验证 Token 有效性 |
| `list_plugins` | `GET /api/v1/models` | 分页获取模型列表 |
| `get_plugin` | `GET /api/v1/models/{namespace}/{name}` | 获取模型详情 |
| `download_plugin` | SDK `snapshot_download()` | 下载模型文件并打包 |
| `check_updates` | `GET /api/v1/models/{namespace}/{name}` | 检查版本更新 |

### 4.2 数据映射

**ModelScope 模型 → RemotePluginInfo：**

| ModelScope 字段 | RemotePluginInfo 字段 | 说明 |
|-----------------|----------------------|------|
| `namespace + name` | `plugin_id` | 格式：namespace/name |
| `name` | `name` | 显示名称 |
| `description` | `description` | 描述 |
| `version / latest_version` | `version` | 版本号 |
| `namespace` | `author` | 作者/命名空间 |
| - | `icon` | ModelScope 无此字段，为 None |
| 用户指定 | `plugin_type` | 同步时由用户指定 |
| `tags` | `tags` | 标签 |
| `downloads` | `downloads` | 下载量 |
| - | `manifest_url` | 为 None |
| SDK 下载路径 | `download_url` | 本地下载路径 |
| `created_at` | `created_at` | 创建时间 |
| `updated_at` | `updated_at` | 更新时间 |

### 4.3 下载流程

```python
async def download_plugin(
    self,
    config: dict,
    plugin_id: str,
    version: str | None = None,
) -> tuple[bytes, str]:
    """下载插件包
    
    流程：
    1. 使用 ModelScope SDK 下载模型到临时目录
    2. 生成 manifest.yaml 文件
    3. 打包为 ZIP 文件
    4. 计算 SHA256 校验和
    5. 返回 (zip_data, checksum)
    """
    from modelscope import snapshot_download
    import tempfile
    import zipfile
    import yaml
    
    # 解析 namespace 和 name
    namespace, name = plugin_id.split("/")
    
    # 下载模型
    local_dir = snapshot_download(
        model_id=plugin_id,
        revision=version or "master",
        api_token=config["auth_config"]["api_token"],
    )
    
    # 生成 manifest
    manifest = {
        "author": namespace,
        "name": name,
        "version": version or "latest",
        "type": "model",  # 将被用户指定的类型覆盖
        "description": f"ModelScope model: {plugin_id}",
    }
    
    # 打包为 ZIP
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
        with zipfile.ZipFile(f, "w") as zf:
            # 添加模型文件
            for root, dirs, files in os.walk(local_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, local_dir)
                    zf.write(file_path, arc_name)
            
            # 添加 manifest.yaml
            zf.writestr("manifest.yaml", yaml.dump(manifest))
        
        zip_data = f.read()
    
    # 计算校验和
    checksum = hashlib.sha256(zip_data).hexdigest()
    
    return zip_data, checksum
```

### 4.4 认证配置

```python
# ModelScope 市场的 auth_config 格式
{
    "api_token": "encrypted:xxxxx"  # ModelScope API Token
}
```

### 4.5 适配器实现

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
        """构建请求头"""
        headers = {"Accept": "application/json"}
        auth_config = config.get("auth_config", {})
        api_token = auth_config.get("api_token", "")
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        return headers

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接"""
        headers = self._build_headers(config)
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/models",
                    headers=headers,
                    params={"page": 1, "page_size": 1},
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
                else:
                    return MarketplaceTestResult(
                        success=False,
                        message=f"连接失败: HTTP {response.status_code}",
                        latency_ms=latency_ms,
                    )
        except httpx.TimeoutException:
            return MarketplaceTestResult(success=False, message="连接超时")
        except Exception as e:
            logger.error(f"测试 ModelScope 市场连接失败: {e}")
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
        headers = self._build_headers(config)

        params: dict[str, Any] = {"Page": page, "PageSize": page_size}
        if keyword:
            params["Name"] = keyword
        if plugin_type:
            params["Task"] = plugin_type

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.API_BASE}/models",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        plugins = []
        models = data.get("Data", {}).get("Models", [])
        for item in models:
            plugins.append(self._parse_model(item))

        total = data.get("Data", {}).get("TotalCount", 0)
        return plugins, total

    async def get_plugin(
        self,
        config: dict,
        plugin_id: str,
    ) -> RemotePluginInfo | None:
        """获取单个插件详情"""
        headers = self._build_headers(config)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/models/{plugin_id}",
                    headers=headers,
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()
                return self._parse_model(data.get("Data", {}))
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
        from modelscope import snapshot_download

        auth_config = config.get("auth_config", {})
        api_token = auth_config.get("api_token", "")

        # 下载模型到临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            local_dir = snapshot_download(
                model_id=plugin_id,
                revision=version or "master",
                api_token=api_token,
                cache_dir=temp_dir,
            )

            # 生成 manifest.yaml
            manifest = {
                "author": plugin_id.split("/")[0],
                "name": plugin_id.split("/")[1] if "/" in plugin_id else plugin_id,
                "version": version or "latest",
                "type": "model",
                "description": f"ModelScope model: {plugin_id}",
            }

            # 打包为 ZIP
            zip_path = os.path.join(temp_dir, "plugin.zip")
            with zipfile.ZipFile(zip_path, "w") as zf:
                # 添加模型文件
                for root, dirs, files in os.walk(local_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, local_dir)
                        zf.write(file_path, arc_name)

                # 添加 manifest.yaml
                zf.writestr("manifest.yaml", yaml.dump(manifest))

            # 读取 ZIP 数据
            with open(zip_path, "rb") as f:
                zip_data = f.read()

        # 计算校验和
        checksum = hashlib.sha256(zip_data).hexdigest()
        return zip_data, checksum

    async def check_updates(
        self,
        config: dict,
        plugins: Sequence[dict],
    ) -> Sequence[PluginUpdateInfo]:
        """检查插件更新"""
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

    def _parse_model(self, item: dict) -> RemotePluginInfo:
        """解析模型数据"""
        namespace = item.get("Namespace", "")
        name = item.get("Name", "")
        plugin_id = f"{namespace}/{name}"

        return RemotePluginInfo(
            plugin_id=plugin_id,
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
        """解析日期时间"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
```

---

## 5. API 设计

### 5.1 同步插件

**请求：**
```http
POST /tenant/admin/v1/marketplaces/sync
Content-Type: application/json

{
  "marketplace_id": "uuid...",
  "plugins": [
    {"plugin_id": "langgenius/ollama", "plugin_type": "model"},
    {"plugin_id": "author/weather-tool", "plugin_type": "tool"}
  ]
}
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "success": [
      {"plugin_id": "langgenius/ollama", "version": "1.2.0"}
    ],
    "failed": [
      {"plugin_id": "author/weather-tool", "message": "下载失败: 连接超时"}
    ],
    "skipped": [
      {"plugin_id": "existing/plugin", "reason": "相同版本已存在"}
    ]
  }
}
```

### 5.2 检查更新

**请求：**
```http
GET /tenant/admin/v1/marketplaces/updates?marketplace_id=uuid...
```

**响应：**
```json
{
  "code": 200,
  "data": [
    {
      "plugin_id": "langgenius/ollama",
      "current_version": "1.0.0",
      "latest_version": "1.2.0",
      "has_update": true
    },
    {
      "plugin_id": "Qwen/Qwen2.5-72B",
      "current_version": "1.0.0",
      "latest_version": "1.0.0",
      "has_update": false
    }
  ]
}
```

### 5.3 应用更新

**请求：**
```http
POST /tenant/admin/v1/marketplaces/updates/langgenius/ollama
Content-Type: application/json

{
  "marketplace_id": "uuid..."
}
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "plugin_id": "langgenius/ollama",
    "old_version": "1.0.0",
    "new_version": "1.2.0",
    "status": "updated"
  }
}
```

### 5.4 Schema 定义

```python
# 同步插件请求
class SyncPluginItem(BaseModel):
    """单个同步插件项"""
    plugin_id: str
    plugin_type: str  # model, tool, agent

class SyncPluginsRequest(BaseModel):
    """同步插件请求"""
    marketplace_id: str
    plugins: list[SyncPluginItem]

# 同步结果
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

class SyncResult(BaseModel):
    """同步结果"""
    success: list[SyncSuccessItem]
    failed: list[SyncFailedItem]
    skipped: list[SyncSkippedItem]

# 更新检查
class PluginUpdateResponse(BaseModel):
    """插件更新响应"""
    plugin_id: str
    current_version: str
    latest_version: str
    has_update: bool

# 应用更新请求
class ApplyUpdateRequest(BaseModel):
    """应用更新请求"""
    marketplace_id: str

# 应用更新结果
class ApplyUpdateResult(BaseModel):
    """应用更新结果"""
    plugin_id: str
    old_version: str
    new_version: str
    status: str  # updated, skipped
```

---

## 6. 前端设计

### 6.1 RemotePluginBrowsePage 修改

**类型选择下拉框：**

每个插件行添加类型选择下拉框，默认为根据市场类型推断的值：
- Dify 市场：从远程数据获取 plugin_type
- ModelScope 市场：默认 "model"，用户可选 "tool"

**同步请求修改：**

```typescript
// 修改前
interface SyncPluginsRequest {
  marketplace_id: string;
  plugin_ids: string[];
}

// 修改后
interface SyncPluginItem {
  plugin_id: string;
  plugin_type: string;
}

interface SyncPluginsRequest {
  marketplace_id: string;
  plugins: SyncPluginItem[];
}
```

### 6.2 同步进度反馈

同步操作显示模态框，实时显示每个插件的处理状态：
- 进行中：显示加载动画
- 成功：显示绿色勾号
- 失败：显示红色叉号和错误信息
- 跳过：显示黄色横线和原因

### 6.3 更新管理入口

在 MarketplaceListPage 添加"检查更新"按钮，点击后：
1. 调用 `GET /marketplaces/updates` 获取可更新列表
2. 弹出模态框显示更新列表
3. 支持单个更新和批量更新

---

## 7. 实现范围

### 7.1 新增文件

| 文件 | 职责 |
|------|------|
| `tenant/services/marketplace/adapters/modelscope_adapter.py` | ModelScope 适配器实现 |
| `tests/tenant/unit/services/marketplace/test_modelscope_adapter.py` | ModelScope 适配器单元测试 |

### 7.2 修改文件

| 文件 | 修改内容 |
|------|----------|
| `tenant/services/marketplace/gateway.py` | 添加 sync_plugins、check_updates、apply_update 方法 |
| `tenant/services/marketplace/adapters/__init__.py` | 导出 ModelScopeAdapter |
| `tenant/services/marketplace/__init__.py` | 导出 ModelScopeAdapter |
| `tenant/schemas/admin/marketplace.py` | 添加同步和更新相关 Schema |
| `tenant/controllers/admin/marketplace_controller.py` | 添加同步、更新 API 端点 |
| `web/vue/src/tenant/types/marketplace.ts` | 修改同步请求类型 |
| `web/vue/src/tenant/api/marketplace.ts` | 添加同步、更新 API 函数 |
| `web/vue/src/tenant/pages/admin/RemotePluginBrowsePage.vue` | 添加类型选择和同步功能 |
| `web/vue/src/tenant/pages/admin/MarketplaceListPage.vue` | 添加检查更新功能 |

### 7.3 依赖变更

```toml
# pyproject.toml 新增依赖
dependencies = [
    # ... 现有依赖
    "modelscope",  # ModelScope SDK，用于下载模型
]
```

### 7.4 优先级

| 功能 | 优先级 | 说明 |
|------|--------|------|
| ModelScope 适配器 | P0 | 核心功能，支持 ModelScope 市场 |
| 插件同步流程 | P0 | 核心功能，完整同步流程 |
| 前端类型选择 | P0 | 同步时指定 plugin_type |
| 更新检查 API | P1 | 检查远程插件是否有新版本 |
| 应用更新 API | P1 | 应用单个插件更新 |
| 前端同步进度 | P1 | 显示同步结果 |
| 前端更新管理 | P2 | 批量检查和应用更新 |

---

## 8. 测试策略

### 8.1 单元测试

| 测试项 | 说明 |
|--------|------|
| ModelScopeAdapter.market_type | 验证返回 "modelscope" |
| ModelScopeAdapter._build_headers | 验证 Token 认证头构建 |
| ModelScopeAdapter._parse_model | 验证模型数据解析 |
| ModelScopeAdapter._parse_datetime | 验证日期解析 |
| Gateway.sync_plugins | 验证同步流程逻辑 |

### 8.2 集成测试

| 测试项 | 说明 |
|--------|------|
| POST /marketplaces/sync | 验证同步 API |
| GET /marketplaces/updates | 验证更新检查 API |
| POST /marketplaces/updates/{id} | 验证应用更新 API |

### 8.3 Mock 策略

由于 ModelScope API 需要网络访问，测试时使用 mock：
- 使用 `pytest-httpx` mock HTTP 请求
- 使用 `unittest.mock.patch` mock SDK 下载

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| ModelScope SDK 不稳定 | 下载失败 | 添加重试机制、详细日志 |
| 大模型下载时间长 | 超时 | 设置合理超时、显示进度 |
| 模型文件过大 | 存储压力 | 仅存储必要的模型文件 |
| API Token 泄露 | 安全风险 | 加密存储、日志脱敏 |
