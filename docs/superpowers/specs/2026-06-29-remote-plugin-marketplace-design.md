# 远程插件市场功能设计规格

## 1. 概述

### 1.1 背景

当前系统的插件定义只能通过本地上传或服务器目录扫描注册，无法从外部插件市场获取插件资源。需要实现远程插件市场功能，支持配置多个外部市场源，获取远程插件列表，选择性同步插件定义，供租户安装使用。

### 1.2 目标

- 支持配置多个远程插件市场（Dify、ModelScope）
- 支持浏览远程市场的插件列表
- 支持选择性同步插件定义到本地
- 支持检测和应用插件更新
- 复用现有插件安装流程

### 1.3 范围

| 包含 | 不包含 |
|------|--------|
| 市场配置管理 | 定时自动同步 |
| 远程插件浏览 | 断点续传 |
| 选择性同步 | 实时同步 |
| 更新检测与应用 | HuggingFace 等其他市场 |
| 认证配置加密 | 多版本共存管理 |

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          远程插件市场功能架构                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  前端层                                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌─────────────────────┐                        │
│  │  市场配置管理页      │    │  远程插件浏览页      │                        │
│  │  - 添加/编辑市场     │    │  - 按市场筛选        │                        │
│  │  - 测试连接         │    │  - 搜索插件          │                        │
│  │  - 启用/禁用        │    │  - 选择同步          │                        │
│  └─────────────────────┘    └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  API 层 (Tenant Admin)                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  POST   /tenant/admin/v1/marketplaces              添加市场配置             │
│  GET    /tenant/admin/v1/marketplaces              市场列表                 │
│  PUT    /tenant/admin/v1/marketplaces/{id}         更新市场配置             │
│  DELETE /tenant/admin/v1/marketplaces/{id}         删除市场配置             │
│  POST   /tenant/admin/v1/marketplaces/{id}/test    测试市场连接             │
│  GET    /tenant/admin/v1/marketplaces/{id}/plugins 浏览远程插件             │
│  POST   /tenant/admin/v1/marketplaces/sync         同步选中插件             │
│  GET    /tenant/admin/v1/marketplaces/updates      检查插件更新             │
│  POST   /tenant/admin/v1/marketplaces/updates/{id} 应用插件更新             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  服务层 (MarketplaceGateway + Adapters)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    MarketplaceGateway                                │   │
│  │  - 管理市场配置                                                      │   │
│  │  - 协调适配器调用                                                    │   │
│  │  - 处理同步流程                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│         ┌────────────────────────────┼────────────────────────────┐        │
│         ▼                            ▼                            ▼        │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐ │
│  │  DifyAdapter    │        │ModelScopeAdapter│        │ (Future...)     │ │
│  └─────────────────┘        └─────────────────┘        └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  数据层                                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  tenant.plugin_marketplaces          市场配置表                             │
│  tenant.plugin_definitions (扩展)    插件定义表（增加来源字段）              │
│  tenant.plugin_packages              插件包存储记录（新增）                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 核心组件

| 组件 | 职责 | 位置 |
|------|------|------|
| MarketplaceGateway | 市场管理入口，协调配置、同步、更新检查 | `tenant/services/marketplace/gateway.py` |
| MarketplaceAdapter | 适配器协议，统一不同市场的接口 | `tenant/services/marketplace/protocol.py` |
| DifyAdapter | Dify 市场适配器实现 | `tenant/services/marketplace/adapters/dify_adapter.py` |
| ModelScopeAdapter | ModelScope 市场适配器实现 | `tenant/services/marketplace/adapters/modelscope_adapter.py` |

---

## 3. 数据模型设计

### 3.1 新增表：plugin_marketplaces（市场配置）

```sql
CREATE TABLE tenant.plugin_marketplaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(64) NOT NULL,              -- 市场名称
    code            VARCHAR(32) NOT NULL UNIQUE,      -- 市场编码
    type            VARCHAR(32) NOT NULL,             -- 市场类型：dify, modelscope
    url             VARCHAR(512) NOT NULL,            -- 市场 API 地址
    auth_type       VARCHAR(16) DEFAULT 'none',       -- 认证类型：none, api_key, token
    auth_config     JSONB DEFAULT '{}',               -- 认证配置（加密存储）
    is_enabled      BOOLEAN DEFAULT TRUE,             -- 是否启用
    sync_config     JSONB DEFAULT '{}',               -- 同步配置
    last_sync_at    TIMESTAMP,                        -- 最后同步时间
    last_sync_status VARCHAR(16),                     -- 最后同步状态
    description     TEXT,                             -- 市场描述
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      UUID,
    updated_by      UUID
);

-- 索引
CREATE INDEX idx_plugin_marketplaces_code ON tenant.plugin_marketplaces(code);
CREATE INDEX idx_plugin_marketplaces_type ON tenant.plugin_marketplaces(type);
CREATE INDEX idx_plugin_marketplaces_enabled ON tenant.plugin_marketplaces(is_enabled);
```

**auth_config 加密存储格式**：

```json
// API Key 类型
{"api_key": "encrypted:xxxxx", "header_name": "X-API-Key"}

// Token 类型
{"token": "encrypted:xxxxx"}

// 无认证
{}
```

### 3.2 新增表：plugin_packages（插件包存储）

```sql
CREATE TABLE tenant.plugin_packages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id       VARCHAR(128) NOT NULL,            -- 插件ID：author/name
    version         VARCHAR(32) NOT NULL,             -- 版本号
    marketplace_id  UUID REFERENCES tenant.plugin_marketplaces(id),
    storage_path    VARCHAR(512) NOT NULL,            -- MinIO 存储路径
    file_size       BIGINT,                           -- 文件大小（字节）
    checksum        VARCHAR(128),                     -- SHA256 校验和
    manifest        JSONB,                            -- 解析后的 manifest
    downloaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(plugin_id, version, marketplace_id)
);

-- 索引
CREATE INDEX idx_plugin_packages_plugin_id ON tenant.plugin_packages(plugin_id);
CREATE INDEX idx_plugin_packages_marketplace ON tenant.plugin_packages(marketplace_id);
```

### 3.3 扩展表：plugin_definitions（插件定义）

在现有表基础上新增字段：

```sql
ALTER TABLE tenant.plugin_definitions ADD COLUMN IF NOT EXISTS
    marketplace_id      UUID REFERENCES tenant.plugin_marketplaces(id),
    remote_plugin_id    VARCHAR(128),                 -- 远程市场的插件标识
    remote_version      VARCHAR(32),                  -- 远程最新版本
    local_version       VARCHAR(32),                  -- 本地存储版本
    update_available    BOOLEAN DEFAULT FALSE,        -- 是否有新版本
    package_id          UUID REFERENCES tenant.plugin_packages(id),
    source_type         VARCHAR(16) DEFAULT 'local';  -- 来源类型：local, remote
```

**字段说明**：

| 字段 | 说明 |
|------|------|
| `marketplace_id` | 来源市场ID，本地注册的为 NULL |
| `remote_plugin_id` | 远程市场的插件ID |
| `remote_version` | 远程市场最新版本号 |
| `local_version` | 本地存储的版本号 |
| `update_available` | 检测到新版本时标记为 true |
| `package_id` | 关联的插件包记录 |
| `source_type` | 区分本地上传和远程同步 |

### 3.4 数据关系

```
plugin_marketplaces (1) ──► (N) plugin_packages
                                        │
                                        ▼
plugin_definitions ◄────────────────────┘
        │
        ▼
plugin_installations (租户安装记录)
```

---

## 4. 适配器协议设计

### 4.1 数据模型

```python
@dataclass
class RemotePluginInfo:
    """远程插件信息"""
    plugin_id: str                    # 插件ID：author/name
    name: str                         # 显示名称
    description: str | None           # 描述
    version: str                      # 版本
    author: str                       # 作者
    icon: str | None                  # 图标 URL
    plugin_type: str                  # tool/model/agent
    tags: list[str]                   # 标签
    downloads: int | None             # 下载量
    manifest_url: str | None          # 清单文件 URL
    download_url: str                 # 下载地址
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class PluginUpdateInfo:
    """插件更新信息"""
    plugin_id: str
    current_version: str              # 当前版本
    latest_version: str               # 最新版本
    has_update: bool                  # 是否有更新
    changelog: str | None             # 更新日志


@dataclass
class MarketplaceTestResult:
    """市场连接测试结果"""
    success: bool
    message: str
    plugin_count: int | None = None   # 可用插件数量
    latency_ms: int | None = None     # 响应延迟
```

### 4.2 适配器协议

```python
class MarketplaceAdapter(Protocol):
    """市场适配器协议"""
    
    @property
    def market_type(self) -> str:
        """市场类型标识：dify, modelscope"""
        ...
    
    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接"""
        ...
    
    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[RemotePluginInfo], int]:
        """获取远程插件列表"""
        ...
    
    async def get_plugin(
        self,
        config: dict,
        plugin_id: str,
    ) -> RemotePluginInfo | None:
        """获取单个插件详情"""
        ...
    
    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """下载插件包，返回 (数据, SHA256校验和)"""
        ...
    
    async def check_updates(
        self,
        config: dict,
        plugins: list[dict],
    ) -> list[PluginUpdateInfo]:
        """检查插件更新"""
        ...
```

### 4.3 Dify 适配器

```python
class DifyAdapter(MarketplaceAdapter):
    """Dify 插件市场适配器"""
    
    @property
    def market_type(self) -> str:
        return "dify"
    
    # 实现所有协议方法...
```

**Dify API 端点**：

| API | 说明 |
|-----|------|
| `GET /plugins` | 获取插件列表 |
| `GET /plugins/{plugin_id}` | 获取插件详情 |
| `GET /plugins/{plugin_id}/download` | 下载插件包 |

### 4.4 ModelScope 适配器

```python
class ModelScopeAdapter(MarketplaceAdapter):
    """ModelScope 模型市场适配器
    
    ModelScope 主要提供模型资源，作为"模型插件"来源。
    """
    
    @property
    def market_type(self) -> str:
        return "modelscope"
    
    # 实现所有协议方法...
```

**ModelScope API 端点**：

| API | 说明 |
|-----|------|
| `GET /models` | 获取模型列表 |
| `GET /models/{namespace}/{name}` | 获取模型详情 |
| `GET /models/{namespace}/{name}/files` | 获取模型文件 |

---

## 5. 服务层设计

### 5.1 MarketplaceGateway

```python
class MarketplaceGateway:
    """插件市场网关服务"""
    
    # 适配器注册表
    _adapters: dict[str, type[MarketplaceAdapter]] = {
        "dify": DifyAdapter,
        "modelscope": ModelScopeAdapter,
    }
    
    # 市场配置管理
    async def create_marketplace(...) -> TenantPluginMarketplace
    async def update_marketplace(...) -> TenantPluginMarketplace
    async def delete_marketplace(...) -> None
    async def list_marketplaces(...) -> list[TenantPluginMarketplace]
    
    # 连接测试
    async def test_connection(...) -> MarketplaceTestResult
    
    # 远程插件浏览
    async def list_remote_plugins(...) -> tuple[list[RemotePluginInfo], int]
    async def get_remote_plugin(...) -> RemotePluginInfo | None
    
    # 插件同步
    async def sync_plugins(...) -> dict[str, Any]
    
    # 更新检查
    async def check_updates(...) -> list[dict[str, Any]]
    async def apply_update(...) -> dict[str, Any]
```

### 5.2 同步流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     插件同步流程                                 │
└─────────────────────────────────────────────────────────────────┘

1. 获取远程插件信息
        │
        ▼
2. 检查本地是否已存在
        │
        ├── 已存在相同版本 ──► 跳过
        │
        ├── 已存在旧版本 ──► 标记 update_available
        │
        ▼
3. 下载插件包
        │
        ▼
4. 解析验证 (plugin_package_service)
        │
        ▼
5. 存储到 MinIO
        │
        ▼
6. 创建 plugin_packages 记录
        │
        ▼
7. 创建/更新 plugin_definitions 记录
        │
        ▼
8. 返回同步结果
```

---

## 6. API 设计

### 6.1 端点列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/tenant/admin/v1/marketplaces` | 添加市场配置 | `tenant:marketplace:write` |
| GET | `/tenant/admin/v1/marketplaces` | 市场列表 | `tenant:marketplace:read` |
| GET | `/tenant/admin/v1/marketplaces/{id}` | 市场详情 | `tenant:marketplace:read` |
| PUT | `/tenant/admin/v1/marketplaces/{id}` | 更新市场配置 | `tenant:marketplace:write` |
| DELETE | `/tenant/admin/v1/marketplaces/{id}` | 删除市场配置 | `tenant:marketplace:write` |
| POST | `/tenant/admin/v1/marketplaces/{id}/test` | 测试市场连接 | `tenant:marketplace:read` |
| GET | `/tenant/admin/v1/marketplaces/{id}/plugins` | 浏览远程插件 | `tenant:marketplace:read` |
| POST | `/tenant/admin/v1/marketplaces/sync` | 同步选中插件 | `tenant:marketplace:write` |
| GET | `/tenant/admin/v1/marketplaces/updates` | 检查插件更新 | `tenant:marketplace:read` |
| POST | `/tenant/admin/v1/marketplaces/updates/{plugin_id}` | 应用插件更新 | `tenant:marketplace:write` |

### 6.2 请求/响应示例

#### 添加市场配置

```http
POST /tenant/admin/v1/marketplaces
Content-Type: application/json

{
  "name": "Dify 官方市场",
  "code": "dify-official",
  "type": "dify",
  "url": "https://plugins.dify.ai/api/v1",
  "auth_type": "none",
  "description": "Dify 官方插件市场"
}
```

```json
{
  "code": 200,
  "data": {
    "id": "uuid...",
    "name": "Dify 官方市场",
    "code": "dify-official",
    "type": "dify",
    "url": "https://plugins.dify.ai/api/v1",
    "auth_type": "none",
    "is_enabled": true,
    "created_at": "2026-06-29T10:00:00Z"
  }
}
```

#### 同步插件

```http
POST /tenant/admin/v1/marketplaces/sync
Content-Type: application/json

{
  "marketplace_id": "uuid...",
  "plugin_ids": ["langgenius/ollama", "author/weather-tool"]
}
```

```json
{
  "code": 200,
  "data": {
    "success": ["langgenius/ollama"],
    "failed": [],
    "skipped": ["author/weather-tool"]
  }
}
```

### 6.3 权限定义

| 权限码 | 名称 | 说明 |
|--------|------|------|
| `tenant:marketplace:read` | 查看插件市场 | 查看、测试、浏览远程插件 |
| `tenant:marketplace:write` | 管理插件市场 | 添加、编辑、删除、同步 |

---

## 7. 配置设计

### 7.1 YAML 配置

```yaml
plugin:
  marketplace:
    sync_timeout: 300           # 同步超时（秒）
    download_timeout: 600       # 下载超时（秒）
    max_concurrent_downloads: 3 # 最大并发下载数
    storage_prefix: "plugins"   # 存储路径前缀
    
    defaults:                   # 预置市场（默认禁用）
      - name: "Dify 官方市场"
        code: "dify-official"
        type: "dify"
        url: "https://plugins.dify.ai/api/v1"
        auth_type: "none"
        enabled: false
      
      - name: "ModelScope 模型市场"
        code: "modelscope"
        type: "modelscope"
        url: "https://modelscope.cn/api/v1"
        auth_type: "none"
        enabled: false
```

---

## 8. 前端页面设计

### 8.1 页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/admin/plugin-marketplaces` | 市场配置列表 | 管理市场配置 |
| `/admin/plugin-marketplaces/{id}/plugins` | 远程插件浏览 | 浏览并同步插件 |

### 8.2 市场配置列表页

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  插件市场管理                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  [+ 添加市场]  [检查更新]                                                    │
│                                                                             │
│  ┌──────────┬────────┬────────┬────────┬──────────┬───────────────────┐    │
│  │ 名称     │ 类型   │ 地址   │ 状态   │ 最后同步 │ 操作              │    │
│  ├──────────┼────────┼────────┼────────┼──────────┼───────────────────┤    │
│  │ Dify官方 │ dify   │ https: │ ✓ 启用 │ 06-29    │ [浏览][同步][编辑]│    │
│  │ ModelScope│models.│ https: │ ○ 禁用 │ -        │ [测试][编辑][删除]│    │
│  └──────────┴────────┴────────┴────────┴──────────┴───────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.3 远程插件浏览页

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  浏览远程插件 - Dify 官方市场                              [← 返回]        │
├─────────────────────────────────────────────────────────────────────────────┤
│  [🔍 搜索插件名称...]    [全部类型 ▼]                                        │
│                                                                             │
│  □ 🤖 Ollama                                    [已同步]                   │
│    langgenius/ollama | v1.0.0 | model                                       │
│    本地大模型供应商，支持 Llama、Qwen 等模型                                 │
│                                                                             │
│  □ 🔧 天气查询工具                              [有更新 ▲]                 │
│    author/weather-tool | v2.1.0 | tool                                      │
│    提供全球城市天气查询功能                                                  │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  已选择 2 个插件                              [同步选中插件]                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. 实施路线图

### 9.1 阶段划分

| 阶段 | 内容 | 预计工时 |
|------|------|----------|
| 1 | 数据层与适配器 | 2-3 天 |
| 2 | 服务层 | 2-3 天 |
| 3 | API 层 | 1-2 天 |
| 4 | 前端页面 | 3-4 天 |
| 5 | 集成测试 | 1-2 天 |

### 9.2 阶段 1 详细任务

| 任务 | 说明 |
|------|------|
| 数据库迁移 | 创建 `plugin_marketplaces`、`plugin_packages` 表 |
| 扩展 plugin_definitions | 添加来源相关字段 |
| 适配器协议 | 定义 Protocol 和数据模型 |
| Dify 适配器 | 完整实现 |
| ModelScope 适配器 | 完整实现 |
| 单元测试 | 适配器测试 |

### 9.3 阶段 2 详细任务

| 任务 | 说明 |
|------|------|
| MarketplaceGateway | 核心服务实现 |
| 同步流程 | 下载、解析、存储、注册 |
| 更新检查 | 版本检测和应用 |
| 认证加密 | 集成加密管理器 |
| 单元测试 | 服务层测试 |

---

## 10. 风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Dify API 不稳定 | 同步失败 | 重试机制、详细日志、手动上传备份 |
| ModelScope 格式转换 | 模型插件解析失败 | 明确支持类型、生成兼容 manifest |
| 网络超时 | 大插件包下载失败 | 分块下载、超时配置 |
| 认证信息泄露 | 安全风险 | 框架加密管理器、日志脱敏 |
| 版本冲突 | 多版本管理复杂 | 当前版本覆盖、记录更新历史 |

---

## 11. 后续迭代方向

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 定时自动同步 | 低 | 按计划自动检查更新 |
| 断点续传 | 低 | 大文件下载支持 |
| HuggingFace 市场 | 低 | 添加更多市场类型 |
| 自定义市场 | 低 | 支持配置通用市场地址 |
| 插件审核流程 | 低 | 同步后需审核才能使用 |
| 同步历史记录 | 低 | 详细日志记录 |

---

## 12. 依赖条件

| 依赖 | 说明 |
|------|------|
| MinIO/OSS | 存储下载的插件包 |
| 框架加密管理器 | 加密市场认证配置 |
| 现有插件系统 | 复用 `plugin_package_service` 解析逻辑 |
| httpx | HTTP 客户端，用于调用远程 API |
