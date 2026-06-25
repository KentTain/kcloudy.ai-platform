# 插件与模型资源管理 Tenant 统一管理设计方案

## 1. 背景与目标

### 1.1 当前问题

插件和模型资源的管理职责分散在 AI 模块，Tenant 模块对这些资源无感知，导致：

- **管理分散**：PluginInstallation 和 ModelProvider 的数据表在 AI 模块，但属于"租户级资源"
- **职责模糊**："有什么"（资源定义）和"用什么"（运行时配置）混在同一张表里
- **配额不可控**：Tenant 模块无法统一分配和限制 AI 资源
- **配置混用**：管理面字段和运行时面字段集中在同一张表（`plugin_installations` 有约 30 个字段）

### 1.2 设计原则

```
Tenant 模块（管理面）     AI 模块（使用面）
"有什么"                  "用什么"
──────────────            ──────────────
插件定义                  插件使用
资源注册表                租户配置
全局元数据                运行时实例
```

**核心思想**：

- Tenant 管资源定义（解决"有什么"的问题）
- AI 管资源使用（解决"用什么"的问题）
- 两个受保护的模块不受影响：`server/python/src/ai_plugin/`（SDK 协议层）、`server/python/src/ai/components/plugin/`（业务逻辑层，仅替换数据访问方式）

---

## 2. 架构总览

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Tenant Schema                                  │
│                                                                             │
│  plugin_definitions (全局插件注册表，合并自 plugins + plugin_declarations)  │
│  ├── 插件注册信息：plugin_id, plugin_unique_identifier                     │
│  ├── 插件声明：declaration (完整 JSONB)                                     │
│  └── 元数据：refers, install_type, manifest_type, remote_declaration        │
│                                                                             │
│  plugin_installations (租户级安装记录，精简管理面字段)                      │
│  ├── 安装标识：tenant_id, plugin_id, plugin_unique_identifier              │
│  ├── 管理配置：plugin_type, status, auto_start, installed_at               │
│  ├── 配置信息：install_config, runtime_config, plugin_config               │
│  └── 策略数据：source, meta, freeze_threshold_hours                        │
│                                                                             │
│  PluginInstallationProvider (Inner API 实现)                                │
│  └── tenant/services/plugin_provider.py                                     │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ get_tenant_installations()
                               │ get_installation()
                               │ create_installation()
                               │ update_installation()
                               │ delete_installation()
                               │
                               │ get_runtime_state()
                               │ update_runtime_state()
                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                               AI Schema                                     │
│                                                                             │
│  plugin_runtime_states (新增，运行时状态)                                   │
│  ├── 进程信息：process_id, port, work_directory                            │
│  ├── 统计信息：call_count, error_count, last_error                         │
│  ├── 时间戳：last_started_at, last_stopped_at, last_accessed_at            │
│  ├── 过期管理：frozen_at, health_check_at                                   │
│  └── 端点统计：endpoints_setups, endpoints_active                          │
│                                                                             │
│  plugin_credentials (保留，凭证 = "怎么用" 的使用配置)                      │
│  ├── 每个租户可为每个插件配置多个凭证                                      │
│  └── 作用域：global / personal（预留）                                     │
│                                                                             │
│  plugin_install_tasks (保留，安装任务管理)                                 │
│  └── 运行时的安装过程跟踪                                                  │
│                                                                             │
│  model_providers (保留，模型供应商凭证)                                     │
│  ├── 每个租户可配置多个供应商凭证                                          │
│  └── plugin_id 通过应用层引用 tenant 安装记录                              │
│                                                                             │
│  model_configs (保留，模型配置)                                            │
│  └── 具体的模型选择 + 调用参数                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 表结构详细设计

### 3.1 tenant.plugin_definitions（新增）

**来源**：合并 `ai.plugins` + `ai.plugin_declarations`
**说明**：全局插件注册表，无 tenant_id，所有租户共享。`plugin_declarations.declaration` 直接成为本表的一个 JSONB 字段，消除重复存储和 JOIN 查询。

```sql
CREATE TABLE tenant.plugin_definitions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id       VARCHAR(128) NOT NULL,
    plugin_unique_identifier VARCHAR(256) NOT NULL UNIQUE,
    declaration     JSONB NOT NULL,
    refers          INTEGER NOT NULL DEFAULT 0,
    install_type    VARCHAR(16) NOT NULL,
    manifest_type   VARCHAR(32),
    remote_declaration JSONB,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_plugin_definitions_plugin_id ON tenant.plugin_definitions(plugin_id);
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `plugin_id` | VARCHAR(128) | 插件 ID，manifest 中的 author+name，例如 `alon/tongyi` |
| `plugin_unique_identifier` | VARCHAR(256) | 插件唯一标识符，格式：`{plugin_id}:{version}@{校验和}` |
| `declaration` | JSONB | **合并自 plugin_declarations**，完整声明内容（manifest + 工具/模型声明） |
| `refers` | INTEGER | 全局引用计数，安装此插件的租户数量 |
| `install_type` | VARCHAR(16) | 安装类型：`local`, `remote` |
| `manifest_type` | VARCHAR(32) | 清单类型 |
| `remote_declaration` | JSONB | 远程声明，远程类型插件时启用 |

### 3.2 tenant.plugin_installations（从 AI 移动并精简）

**来源**：从 `ai.plugin_installations` 移动，**剥离**运行时字段到 `ai.plugin_runtime_states`

```sql
CREATE TABLE tenant.plugin_installations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL,
    plugin_id       VARCHAR(128) NOT NULL,
    plugin_unique_identifier VARCHAR(256) NOT NULL,
    plugin_type     VARCHAR(16) NOT NULL,
    status          VARCHAR(16) NOT NULL DEFAULT 'active',
    auto_start      BOOLEAN NOT NULL DEFAULT FALSE,
    installed_at    TIMESTAMP WITH TIME ZONE,
    install_config  JSONB,
    runtime_config  JSONB,
    plugin_config   JSONB,
    source          VARCHAR(16),
    meta            JSONB,
    freeze_threshold_hours INTEGER NOT NULL DEFAULT 24,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (tenant_id, plugin_id)
);

CREATE INDEX idx_tenant_installations_tenant_id ON tenant.plugin_installations(tenant_id);
CREATE INDEX idx_tenant_installations_plugin_id ON tenant.plugin_installations(plugin_id);
CREATE INDEX idx_tenant_installations_status ON tenant.plugin_installations(status);
```

| 字段 | 类型 | 归属 | 说明 |
|------|------|------|------|
| `tenant_id` | VARCHAR(36) | 租户 | 租户标识 |
| `plugin_id` | VARCHAR(128) | 插件 | 如 `alon/tongyi` |
| `plugin_unique_identifier` | VARCHAR(256) | 版本 | 版本 + 校验和 |
| `plugin_type` | VARCHAR(16) | 管理 | 插件类型：`tool`, `model`, `agent` |
| `status` | VARCHAR(16) | **管理** | `active`（启用）/ `inactive`（禁用） |
| `auto_start` | BOOLEAN | **管理** | 是否在服务重启后自动启动 |
| `installed_at` | TIMESTAMP | **管理** | 安装完成时间 |
| `install_config` | JSONB | **管理** | 安装时的配置信息（依赖版本、环境信息等） |
| `runtime_config` | JSONB | 配置 | 持久化的运行时配置（跨重启保留） |
| `plugin_config` | JSONB | **交叉** | **关键共享字段**。完整 PluginConfig，Tenant 管理定义，AI 通过 Provider 获取 |
| `source` | VARCHAR(16) | **管理** | 来源：`package`, `marketplace` |
| `meta` | JSONB | **管理** | 元数据，marketplace 记录插件的 meta 信息 |
| `freeze_threshold_hours` | INTEGER | **管理** | 冻结阈值（小时），管理策略 |

### 3.3 ai.plugin_runtime_states（新增）

**来源**：从 `ai.plugin_installations` 拆分出运行时字段

```sql
CREATE TABLE ai.plugin_runtime_states (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL,
    plugin_id       VARCHAR(128) NOT NULL,
    process_id      INTEGER,
    port            INTEGER,
    work_directory  VARCHAR(512),
    call_count      INTEGER NOT NULL DEFAULT 0,
    error_count     INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT,
    last_started_at TIMESTAMP WITH TIME ZONE,
    last_stopped_at TIMESTAMP WITH TIME ZONE,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    frozen_at       TIMESTAMP WITH TIME ZONE,
    health_check_at TIMESTAMP WITH TIME ZONE,
    endpoints_setups INTEGER NOT NULL DEFAULT 0,
    endpoints_active INTEGER NOT NULL DEFAULT 0,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (tenant_id, plugin_id)
);

CREATE INDEX idx_runtime_states_tenant_id ON ai.plugin_runtime_states(tenant_id);
CREATE INDEX idx_runtime_states_plugin_id ON ai.plugin_runtime_states(plugin_id);
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `tenant_id` | VARCHAR(36) | 租户标识 |
| `plugin_id` | VARCHAR(128) | 插件 ID |
| `process_id` | INTEGER | 运行时进程 PID |
| `port` | INTEGER | 运行时监听端口 |
| `work_directory` | VARCHAR(512) | 运行时工作目录 |
| `call_count` | INTEGER | 调用次数统计 |
| `error_count` | INTEGER | 错误次数统计 |
| `last_error` | TEXT | 最后错误信息 |
| `last_started_at` | TIMESTAMP | 最后启动时间 |
| `last_stopped_at` | TIMESTAMP | 最后停止时间 |
| `last_accessed_at` | TIMESTAMP | 最近访问时间（用于冻结判断） |
| `frozen_at` | TIMESTAMP | 冻结时间 |
| `health_check_at` | TIMESTAMP | 最后健康检查时间 |
| `endpoints_setups` | INTEGER | 端点设置数 |
| `endpoints_active` | INTEGER | 活跃端点数 |

### 3.4 保留在 AI 的表（不做 schema 迁移）

| 表名 | Schema | 说明 | 不动原因 |
|------|--------|------|----------|
| `plugin_credentials` | `ai` | 凭证管理（多凭证池） | 凭证是"怎么用"的使用配置 |
| `plugin_install_tasks` | `ai` | 安装任务跟踪 | 安装是运行时过程管理 |
| `model_providers` | `ai` | 模型供应商凭证 | 凭证是使用配置，与模型调用紧密相关 |
| `model_configs` | `ai` | 模型配置 | 模型选择 + 参数是运行时使用配置 |

---

## 4. 字段映射表

### 4.1 plugin_installations 拆分映射

```
当前 ai.plugin_installations        迁移目标
──────────────────────────────────  ──────────────────────────────
tenant_id                           → tenant.plugin_installations.tenant_id
plugin_id                           → tenant.plugin_installations.plugin_id
plugin_unique_identifier            → tenant.plugin_installations.plugin_unique_identifier
runtime_type                        → (弃用，由 PluginManager 运行时决定)
plugin_type                         → tenant.plugin_installations.plugin_type
status                              → tenant.plugin_installations.status (管理语义)
installed_at                        → tenant.plugin_installations.installed_at
last_started_at                     → ai.plugin_runtime_states.last_started_at
last_stopped_at                     → ai.plugin_runtime_states.last_stopped_at
last_accessed_at                    → ai.plugin_runtime_states.last_accessed_at
frozen_at                           → ai.plugin_runtime_states.frozen_at
process_id                          → ai.plugin_runtime_states.process_id
port                                → ai.plugin_runtime_states.port
work_directory                      → ai.plugin_runtime_states.work_directory
call_count                          → ai.plugin_runtime_states.call_count
error_count                         → ai.plugin_runtime_states.error_count
last_error                          → ai.plugin_runtime_states.last_error
health_check_at                     → ai.plugin_runtime_states.health_check_at
install_config                      → tenant.plugin_installations.install_config
runtime_config                      → tenant.plugin_installations.runtime_config
auto_start                          → tenant.plugin_installations.auto_start
freeze_threshold_hours              → tenant.plugin_installations.freeze_threshold_hours
endpoints_setups                    → ai.plugin_runtime_states.endpoints_setups
endpoints_active                    → ai.plugin_runtime_states.endpoints_active
source                              → tenant.plugin_installations.source
meta                                → tenant.plugin_installations.meta
plugin_config                       → tenant.plugin_installations.plugin_config (通过 Provider 供 AI 读取)
```

### 4.2 plugins + plugin_declarations 合并映射

```
当前 ai.plugins                  迁移目标
──────────────────────────────   ──────────────────────────────
plugin_id                        → tenant.plugin_definitions.plugin_id
plugin_unique_identifier         → tenant.plugin_definitions.plugin_unique_identifier
refers                           → tenant.plugin_definitions.refers
install_type                     → tenant.plugin_definitions.install_type
manifest_type                    → tenant.plugin_definitions.manifest_type
remote_declaration               → tenant.plugin_definitions.remote_declaration
(无此字段)                       → tenant.plugin_definitions.declaration

当前 ai.plugin_declarations     迁移目标
──────────────────────────────   ──────────────────────────────
plugin_id                        → tenant.plugin_definitions.plugin_id
plugin_unique_identifier         → tenant.plugin_definitions.plugin_unique_identifier
declaration                      → tenant.plugin_definitions.declaration
```

---

## 5. Inner API 设计

### 5.1 协议定义位置

`framework/tenant/plugin_protocols.py`

遵循已有的 `TenantProvider` 模式（`server/python/src/framework/tenant/protocols.py`），在 `framework/tenant/` 目录下新增协议定义。

### 5.2 PluginInstallationDTO

```python
@dataclass
class PluginInstallationDTO:
    """Tenant 模块返回给 AI 模块的插件安装信息"""
    plugin_id: str
    plugin_unique_identifier: str
    plugin_type: str
    status: str                    # ACTIVE/INACTIVE (管理语义)
    auto_start: bool
    installed_at: datetime | None
    plugin_config: dict | None     # 关键共享字段
    runtime_config: dict | None
    install_config: dict | None
    source: str | None
    meta: dict | None
    freeze_threshold_hours: int
```

### 5.3 PluginRuntimeStateDTO

```python
@dataclass
class PluginRuntimeStateDTO:
    """AI 模块的插件运行时状态（由 AI 写入，Tenant 通过 Provider 只读获取）"""
    tenant_id: str
    plugin_id: str
    process_id: int | None
    port: int | None
    work_directory: str | None
    call_count: int
    error_count: int
    last_error: str | None
    last_started_at: datetime | None
    last_stopped_at: datetime | None
    last_accessed_at: datetime | None
    frozen_at: datetime | None
    health_check_at: datetime | None
    endpoints_setups: int
    endpoints_active: int
```

### 5.4 PluginInstallationProvider 协议

```python
class PluginInstallationProvider(Protocol):
    """插件安装提供者协议
    Tenant 模块实现此协议，AI 模块通过框架全局注册获取实例。
    实现依赖倒置，避免 AI → Tenant 的模块耦合。
    """

    # ========== 管理面操作（CRUD） ==========

    async def get_tenant_installations(
        self, tenant_id: str
    ) -> list[PluginInstallationDTO]:
        """获取租户的所有活跃插件安装"""
        ...

    async def get_installation(
        self, tenant_id: str, plugin_id: str
    ) -> PluginInstallationDTO | None:
        """获取单个插件安装信息"""
        ...

    async def create_installation(
        self, tenant_id: str, data: PluginInstallationDTO
    ) -> PluginInstallationDTO:
        """创建插件安装记录"""
        ...

    async def update_installation(
        self, tenant_id: str, plugin_id: str, data: dict
    ) -> PluginInstallationDTO:
        """更新插件安装的管理字段（如 status, auto_start 等）"""
        ...

    async def delete_installation(
        self, tenant_id: str, plugin_id: str
    ) -> None:
        """删除插件安装记录"""
        ...

    # ========== 运行时状态操作（AI 侧） ==========

    async def get_runtime_state(
        self, tenant_id: str, plugin_id: str
    ) -> PluginRuntimeStateDTO | None:
        """获取插件运行时状态"""
        ...

    async def update_runtime_state(
        self, tenant_id: str, plugin_id: str, state: dict
    ) -> None:
        """更新插件运行时状态"""
        ...

    async def delete_runtime_state(
        self, tenant_id: str, plugin_id: str
    ) -> None:
        """删除插件运行时状态（卸载时清理）"""
        ...
```

### 5.5 全局注册模式

```python
_plugin_installation_provider: PluginInstallationProvider | None = None

def register_plugin_installation_provider(provider: PluginInstallationProvider) -> None:
    """注册插件安装提供者，应用启动时调用"""
    global _plugin_installation_provider
    _plugin_installation_provider = provider

def get_plugin_installation_provider() -> PluginInstallationProvider:
    """获取插件安装提供者"""
    if _plugin_installation_provider is None:
        raise RuntimeError("PluginInstallationProvider not registered")
    return _plugin_installation_provider
```

### 5.6 Tenant 模块实现

`tenant/services/plugin_provider.py`

```python
class PluginInstallationProviderImpl(PluginInstallationProvider):
    """Tenant 模块对 PluginInstallationProvider 的实现
    直接访问 tenant schema 的数据表。
    """

    async def get_tenant_installations(
        self, tenant_id: str
    ) -> list[PluginInstallationDTO]:
        """查询 tenant.plugin_installations 表，构建 DTO"""
        async with get_task_session() as session:
            result = await session.execute(
                select(TenantPluginInstallation).where(
                    TenantPluginInstallation.tenant_id == tenant_id
                )
            )
            records = result.scalars().all()
            return [self._to_dto(r) for r in records]

    async def get_runtime_state(
        self, tenant_id: str, plugin_id: str
    ) -> PluginRuntimeStateDTO | None:
        """跨 schema 查询 ai.plugin_runtime_states（Tenant 模块有跨 schema 读权限）"""
        # 实现方式：通过同一个数据库连接查询 ai schema
        ...

    # ... 其他方法实现
```

---

## 6. 对核心模块的影响分析

### 6.1 PluginManager (ai/components/plugin/engine/core/plugin_manager.py)

**原则**：不改业务逻辑，仅替换数据访问方式（ORM → Provider）

#### 变化点 A：加载元数据

```python
# 修改前
async def _load_plugins_metadata_from_database(self, session):
    result = await session.execute(
        select(PluginInstallation).where(
            and_(
                PluginInstallation.tenant_id == self.tenant_id,
                PluginInstallation.status != PluginStatus.INACTIVE,
            ),
        ),
    )
    installations = result.scalars().all()
    for installation in installations:
        plugin_info = await self._load_plugin_info_from_installation(installation)
        self.plugins[plugin_info.plugin_id] = plugin_info

# 修改后
async def _load_plugins_metadata_from_database(self, session):
    provider = get_plugin_installation_provider()
    installations = await provider.get_tenant_installations(self.tenant_id)
    for installation in installations:
        runtime_state = await provider.get_runtime_state(
            self.tenant_id, installation.plugin_id
        )
        plugin_info = await self._load_plugin_info_from_installation(
            installation, runtime_state
        )
        if plugin_info:
            self.plugins[installation.plugin_id] = plugin_info
```

#### 变化点 B：加载 PluginInfo

```python
# 修改前
async def _load_plugin_info_from_installation(self, installation):
    plugin_info = PluginInfo(
        config=installation.plugin_config,  # ORM 对象属性
        status=installation.status,
        installed_at=installation.installed_at,
        started_at=installation.last_started_at,
    )
    return plugin_info

# 修改后
async def _load_plugin_info_from_installation(
    self, installation: PluginInstallationDTO, runtime_state: PluginRuntimeStateDTO | None
):
    plugin_info = PluginInfo(
        config=installation.plugin_config,  # DTO 对象属性
        status=installation.status,
        installed_at=installation.installed_at,
        started_at=runtime_state.last_started_at if runtime_state else None,
    )
    return plugin_info
```

#### 变化点 C：保存安装记录

```python
# 修改前
async def _save_plugin_installation_to_database(self, session, plugin_config, ...):
    installation = PluginInstallation(**filtered_kwargs)
    session.add(installation)
    await session.flush()

# 修改后
async def _save_plugin_installation_to_database(self, session, plugin_config, ...):
    # 1. 通过 Provider 写入 tenant.plugin_installations（管理面）
    provider = get_plugin_installation_provider()
    dto = await provider.create_installation(tenant_id, PluginInstallationDTO(...))

    # 2. 写入 ai.plugin_runtime_states（运行时面）
    runtime_state = PluginRuntimeState(
        tenant_id=tenant_id,
        plugin_id=plugin_id,
        # ... 初始化运行时字段
    )
    session.add(runtime_state)
    await session.flush()
```

#### 其他需调整的地方

| PluginManager 方法 | 当前行为 | 改动 |
|---|---|---|
| `_check_duplicate_installation()` | ORM 查询 PluginInstallation | → Provider 查询 |
| `_ensure_plugin_ready()` | ORM 查询状态 | → Provider 查询 |
| `start_plugin()` | 写入 last_started_at, process_id, port | → 写入 plugin_runtime_states |
| `stop_plugin()` | 写入 status, last_stopped_at | status → Provider, last_stopped_at → runtime_states |

### 6.2 PluginManagementService (ai/services/plugin.py)

| 方法 | 当前 ORM 访问 | 改动 |
|---|---|---|
| `get_plugin_list()` | `select(PluginInstallation)` | → Provider |
| `get_plugin_info()` | `select(PluginInstallation)` | → Provider |
| `get_plugin_credentials_schema()` | ORM 读取 plugin_config | → Provider 获取 plugin_config |
| `create_credential()` | ORM 读取 plugin_config | → Provider 获取 plugin_config |
| `uninstall_plugin()` | ORM 删除记录 | → Provider 删除 + 删除 runtime_states |

### 6.3 ModelClient (ai/components/plugin/client/model_client.py)

**无需改动**。`fetch_model_providers()` 读取 `plugin_manager.plugins`（内存缓存），不直接访问数据库。数据来源变化对它是透明的。

### 6.4 ai_plugin (server/python/src/ai_plugin/)

**完全不受影响**。`ai_plugin` 是 SDK 协议层，只定义接口实体（`AIModelEntity`, `PromptMessage` 等），不访问任何数据表。

---

## 7. 实施路线图

### 阶段 P0：基础设施（新增代码）

| 步骤 | 文件 | 内容 |
|------|------|------|
| 1 | `framework/tenant/plugin_protocols.py` | 定义 PluginInstallationDTO、PluginRuntimeStateDTO、PluginInstallationProvider 协议 |
| 2 | `tenant/models/plugin_definition.py` | 定义 TenantPluginDefinition ORM 模型 |
| 3 | `tenant/models/plugin_installation.py` | 定义 TenantPluginInstallation ORM 模型 |
| 4 | `tenant/services/plugin_provider.py` | 实现 PluginInstallationProviderImpl |
| 5 | 应用入口处 | 注册 Provider (`register_plugin_installation_provider()`) |
| 6 | `ai/models/plugin_runtime_state.py` | 定义 PluginRuntimeState ORM 模型 |

### 阶段 P1：数据迁移

| 步骤 | 内容 |
|------|------|
| 1 | 编写 Alembic migration：创建 `tenant.plugin_definitions`、`tenant.plugin_installations`、`ai.plugin_runtime_states` 表 |
| 2 | 迁移 `ai.plugins` + `ai.plugin_declarations` → `tenant.plugin_definitions` |
| 3 | 迁移 `ai.plugin_installations` → `tenant.plugin_installations` + `ai.plugin_runtime_states` |
| 4 | 保留旧表（双向兼容，允许回滚） |

### 阶段 P2：代码替换

| 步骤 | 文件 | 影响范围 |
|------|------|----------|
| 1 | `plugin_manager.py` | 替换 `_load_plugins_metadata_from_database()` 和 `_load_plugin_info_from_installation()` |
| 2 | `plugin_manager.py` | 替换 `_save_plugin_installation_to_database()` 和 `_check_duplicate_installation()` |
| 3 | `plugin_manager.py` | 替换 `_ensure_plugin_ready()` 和启动/停止中的状态写入 |
| 4 | `plugin_manager.py` | 替换 `stop_plugin()` 和 `uninstall_plugin()` 中的状态管理 |
| 5 | `ai/services/plugin.py` | 替换所有 ORM 查询 → Provider 调用 |

### 阶段 P3：清理

| 步骤 | 内容 |
|------|------|
| 1 | 确认功能正常运行后，删除旧表（`ai.plugins`, `ai.plugin_declarations`, `ai.plugin_installations`） |
| 2 | 删除 `ai/models/plugin.py` 中已迁移的模型定义（`Plugin`, `PluginDeclaration`, `PluginInstallation`） |
| 3 | 删除 `ai/models/__init__.py` 中的旧模型导出 |

### 阶段 P4（可选）：权限管理

按需求文档第 8 节，注册 AI Module 的权限定义（`ai:plugin:install`, `ai:model:configure` 等）。

---

## 8. 风险与注意事项

### 8.1 事务一致性

**写操作涉及两个 Schema**：安装/卸载插件时，需要同时写 `tenant.plugin_installations`（通过 Provider）和 `ai.plugin_runtime_states`（直接 ORM）。如果这两个操作不在同一个数据库事务中，可能出现数据不一致。

**解决方案**：

- `Provider.create_installation()` 接受一个可选的 `session` 参数，用于将 Tenant 侧的写入纳入 AI 侧的事务
- 或者，使用两阶段提交 / 补偿事务机制

建议优先方案：

```python
# Tenant side (via Provider)
async def create_installation(
    self, tenant_id: str, data: PluginInstallationDTO,
    session: AsyncSession | None = None  # 可选：接入调用者的事务
) -> PluginInstallationDTO:
    ...

# AI side
async def _save_plugin_installation_to_database(self, session, ...):
    provider = get_plugin_installation_provider()
    # 传入 session，让 Tenant 写入共享同一事务
    dto = await provider.create_installation(tenant_id, data, session=session)
    runtime = PluginRuntimeState(...)
    session.add(runtime)
    await session.flush()
```

### 8.2 缓存一致性

`PluginManager.plugins` 是内存缓存，从 Provider 加载。如果其他进程修改了 `tenant.plugin_installations`（如 Web 管理端禁用了插件），当前进程的插件管理器感知不到。

**乐观策略**（当前已存在）：缓存 TTL = 60 秒，过期后重新从 Provider 加载。

### 8.3 最小改动原则

- `PluginInfo` 的构造逻辑不变（字段映射关系不变）
- `PluginManager` 的运行时流程（安装→注册→启动→调用→停止→卸载）不变
- 仅替换数据读取的来源：ORM 对象 → DTO 对象
- 不对 `ai_plugin/` 做任何修改
- 不对 `ModelClient` 做任何修改

### 8.4 model_providers 的 plugin_id 引用

`model_providers.plugin_id` 引用的是 `tenant.plugin_installations.plugin_id`（字符串语义，非 DB 外键）。当前实现中 `model_providers.plugin_id` 已经是无约束的 VARCHAR 类型（仅有索引），此模式保持不变。

---

## 9. 附录：数据库 Schema 对比

### 迁移前

```
ai schema:
├── plugins (全局插件元数据)
├── plugin_declarations (插件声明)
├── plugin_installations (安装记录，含管理和运行时字段混用)
├── plugin_install_tasks (安装任务)
├── plugin_credentials (凭证)
├── model_providers (模型供应商)
└── model_configs (模型配置)
```

### 迁移后

```
tenant schema:
├── plugin_definitions (全局插件注册表，合并 plugins + plugin_declarations)
├── plugin_installations (安装记录，仅管理面字段)
└── ... 其他已有表（tenants, database_configs, modules 等）

ai schema:
├── plugin_runtime_states (新增，仅运行时字段)
├── plugin_credentials (保留)
├── plugin_install_tasks (保留)
├── model_providers (保留)
├── model_configs (保留)
└── ... 其他已有 AI 表
```

### 数据量变化

| 表 | 迁移前字段数 | 迁移后字段数 | 变化 |
|---|---|---|---|
| `plugins` | 7 | (合并) | 归入 `plugin_definitions` |
| `plugin_declarations` | 3 | (合并) | 归入 `plugin_definitions` |
| `plugin_installations` | ~30 | 16 (Tenant 侧) | -46% |
| `plugin_runtime_states` | (新增) | 16 (AI 侧) | 从安装表剥离 |
| `plugin_credentials` | 8 | 8 | 不变 |
| `plugin_install_tasks` | 6 | 6 | 不变 |
| `model_providers` | 6 | 6 | 不变 |
| `model_configs` | 6 | 6 | 不变 |
