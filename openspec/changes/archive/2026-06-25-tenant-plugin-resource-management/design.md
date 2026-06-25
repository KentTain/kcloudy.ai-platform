## 上下文

### 当前状态

插件和模型资源管理存在以下问题：

- **职责分散**：`PluginInstallation` 和 `ModelProvider` 数据表在 AI 模块，但属于"租户级资源"
- **职责模糊**："有什么"（资源定义）和"用什么"（运行时配置）混在同一张表（`plugin_installations` 约 30 个字段）
- **配额不可控**：Tenant 模块无法统一分配和限制 AI 资源

### 约束

- Tenant 和 AI 模块使用独立的 Session，无法在同一个事务中完成跨 Schema 操作
- 无历史数据迁移需求
- 当前阶段不考虑插件卸载时的 `refers` 字段减少
- 插件版本统一管理：一个 `plugin_id` = 一个版本

### 利益相关者

- **Tenant 模块**：负责资源定义和安装记录管理
- **AI 模块**：负责插件配置和运行时状态管理
- **Web 管理端**：需要展示插件定义列表和引用租户数

## 目标 / 非目标

**目标：**

1. 实现职责分离：Tenant 管资源定义（"有什么"），AI 管资源使用（"用什么"）
2. Tenant 模块能够感知和管理插件资源，为后续配额管理奠定基础
3. 通过 Provider 协议实现依赖倒置，避免 AI → Tenant 的模块耦合
4. 保持 AI 模块核心业务逻辑不变，仅替换数据访问方式

**非目标：**

1. 不实现租户级资源配额限制（后续迭代）
2. 不支持插件多版本共存（统一版本管理）
3. 不处理插件卸载时的 `refers` 字段减少
4. 不修改 `ai_plugin` SDK 协议层

## 决策

### 决策 1：数据模型拆分策略

**选择：按职责拆分到不同 Schema**

```
Tenant Schema (管理面)       AI Schema (使用面)
"有什么"                     "用什么"
──────────────               ──────────────
plugin_definitions           plugin_configs
plugin_installations         plugin_runtime_states
```

**替代方案：**

- 方案 A：所有表保留在 AI Schema，Tenant 模块通过视图访问
  - 缺点：未解决职责分离问题，配额管理仍困难

- 方案 B：所有表迁移到 Tenant Schema，AI 模块通过 API 访问
  - 缺点：AI 模块频繁访问 Tenant，性能开销大

**理由：** 当前选择实现了最清晰的职责边界，同时保持 AI 模块的运行时性能。

### 决策 2：跨模块通信方式

**选择：Provider 协议 + 事件驱动**

```python
# Provider 协议（同步操作）
class PluginInstallationProvider(Protocol):
    async def get_installation(tenant_id: str, plugin_id: str) -> PluginInstallationDTO | None
    async def create_installation(tenant_id: str, data: PluginInstallationDTO) -> PluginInstallationDTO
    async def update_installation(tenant_id: str, plugin_id: str, data: dict) -> PluginInstallationDTO
    async def delete_installation(tenant_id: str, plugin_id: str) -> None

# 事件驱动（异步补偿）
@dataclass
class PluginInstallationFailed:
    tenant_id: str
    plugin_id: str
    error_message: str
```

**替代方案：**

- 方案 A：共享 Session，跨 Schema 事务
  - 缺点：违反模块边界，Tenant 不能接受 AI 的 Session

- 方案 B：HTTP Inner API
  - 缺点：当前单体应用不需要网络开销，后续独立部署时再迁移

**理由：** Provider 协议零开销，依赖倒置清晰，且为未来 Inner API 迁移预留接口签名一致性。

### 决策 3：状态机设计

**选择：四状态模型**

```
PENDING → ACTIVE / FAILED
ACTIVE ↔ INACTIVE
FAILED → 定时清理（24h）
```

| 状态 | 说明 | 触发者 |
|-----|------|-------|
| PENDING | 安装中，Tenant 记录已创建 | PluginManager |
| ACTIVE | 已启用，AI 配置已就绪 | PluginManager |
| INACTIVE | 已禁用 | Web API |
| FAILED | 安装失败，可清理 | PluginManager / 定时任务 |

**理由：** PENDING 状态用于标识"孤儿记录"，支持通过状态控制清理策略。

### 决策 4：refers 字段维护

**选择：安装时递增，暂不处理卸载**

```python
async def _ensure_plugin_definition(session, plugin_config):
    definition = await session.execute(
        select(TenantPluginDefinition).where(
            TenantPluginDefinition.plugin_id == plugin_config.plugin_id
        )
    )
    if definition.scalar_one_or_none():
        definition.refers += 1  # 存在：递增
    else:
        definition = TenantPluginDefinition(
            plugin_id=plugin_config.plugin_id,
            refers=1,  # 不存在：初始为 1
            ...
        )
```

**理由：** 当前阶段无卸载需求，简化实现。`refers` 字段用于统计展示，非关键业务逻辑，后续可扩展。

### 决策 5：Web 管理端数据获取

**选择：只查询 Tenant Schema**

Tenant Web 管理端只展示 `plugin_definitions` 列表，不涉及跨模块查询。插件安装状态由 AI 模块管理，通过 AI 的 API 查询。

**理由：** 保持 Tenant 模块的独立性，避免复杂的跨模块数据组装。

## 风险 / 权衡

### 风险 1：事件驱动一致性

**风险：** AI 侧创建失败后，Tenant 侧记录已存在，产生"孤儿记录"。

**缓解措施：**

1. PENDING 状态标识安装中的记录
2. 失败时更新为 FAILED 状态
3. 定时任务清理超过 24 小时的 FAILED 记录

```python
# 定时清理任务
@scheduled_task(interval_hours=1)
async def cleanup_failed_installations():
    async with get_task_session() as session:
        await session.execute(
            delete(TenantPluginInstallation).where(
                and_(
                    TenantPluginInstallation.status == "FAILED",
                    TenantPluginInstallation.created_at < datetime.utcnow() - timedelta(hours=24)
                )
            )
        )
```

### 风险 2：缓存一致性

**风险：** `PluginManager.plugins` 内存缓存，其他进程修改 `plugin_installations` 后，当前进程需等待 TTL 过期才能感知。

**缓解措施：**

- 当前 TTL = 60 秒（已有策略）
- 乐观假设：插件安装/卸载为低频操作
- 后续可引入事件驱动的缓存失效机制

### 风险 3：状态更新时机

**风险：** 安装流程中，Tenant 侧记录创建成功，AI 侧配置创建失败，状态如何回滚？

**缓解措施：**

```python
async def install_plugin(self, session, plugin_package, install_request):
    try:
        # 1. Provider 创建 PENDING 记录
        installation = await provider.create_installation(
            tenant_id,
            PluginInstallationDTO(status="PENDING", ...)
        )

        # 2. AI 侧创建配置
        session.add_all([plugin_config, runtime_state])
        await session.flush()

        # 3. 成功：更新为 ACTIVE
        await provider.update_installation(
            tenant_id, plugin_id, {"status": "ACTIVE"}
        )

    except Exception as e:
        # 4. 失败：更新为 FAILED
        await provider.update_installation(
            tenant_id, plugin_id, {"status": "FAILED", "error": str(e)}
        )
        raise
```

### 权衡：表拆分粒度

**选择：** `plugin_installations` 拆成 3 张表（Tenant 安装 + AI 配置 + AI 运行时）

**权衡：**

- 优点：职责清晰，符合单一职责原则
- 缺点：查询需要 JOIN，但插件管理为低频操作，性能影响可接受

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                   数据访问架构                                   │
└─────────────────────────────────────────────────────────────────┘

PluginManager (AI 模块)
         │
         │ 1. Provider 查询安装记录
         ▼
┌─────────────────────────┐
│ PluginInstallationProvider (协议)│
└───────────┬─────────────┘
            │
            │ 实现
            ▼
┌─────────────────────────┐
│ PluginInstallationProviderImpl │
│ (Tenant 模块)                   │
└───────────┬─────────────┘
            │
            │ 独立 Session
            ▼
┌─────────────────────────┐
│ tenant.plugin_installations     │
│ tenant.plugin_definitions       │
└─────────────────────────┘

         │ 2. AI 侧查询配置
         ▼
┌─────────────────────────┐
│ ai.plugin_configs               │
│ ai.plugin_runtime_states        │
└─────────────────────────┘
```
