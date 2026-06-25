## 上下文

### 背景

当前插件管理职责分散在 AI 模块，存在以下问题：
- **数据分散**：`ai.plugins`、`ai.plugin_declarations`、`ai.plugin_installations` 三张表职责不清
- **字段混用**：`plugin_installations` 表同时包含管理字段和运行时字段（约 30 个字段）
- **跨模块访问困难**：Tenant 模块无法感知插件资源，无法实现配额管理

### 约束

- AI 模块不能直接访问 Tenant Schema 的数据库表
- Tenant 模块不能依赖 AI 模块
- 需要保证跨模块操作的数据一致性

### 设计基础

本文档基于《插件与模型资源管理 Tenant 统一管理设计方案》（docs/designs/3.插件与模型资源管理 Tenant 统一管理设计方案.md）和《插件管理功能设计方案》（docs/designs/4.插件管理功能设计方案.md）。

## 目标 / 非目标

**目标：**

1. Tenant 模块实现插件定义管理（注册、查询、标记、统计）
2. AI 模块重构为通过 Provider 访问 Tenant 数据
3. 实现事件驱动的安装流程，保证跨模块一致性
4. 提供完整的运行时监控能力

**非目标：**

1. 本迭代不支持插件配额管理（后续迭代）
2. 本迭代不支持插件市场（后续迭代）
3. 本迭代只支持 `shared` 安装类型（`.venv`、`docker` 后续迭代）

## 决策

### 决策 1：Schema 分离策略

**选择**：将插件数据表按职责分离到不同 Schema

```
tenant schema:
├── plugin_definitions (全局插件注册表)
└── plugin_installations (租户安装记录，仅管理字段)

ai schema:
├── plugin_configs (插件配置)
├── plugin_runtime_states (运行时状态)
├── plugin_credentials (凭证)
└── plugin_install_tasks (安装任务)
```

**理由**：
- Tenant 负责"有什么"（定义、安装记录）
- AI 负责"用什么"（配置、状态）
- 职责清晰，便于后续扩展

**替代方案**：
- 保留单表：字段过多，职责不清
- 完全迁移到 Tenant：AI 模块无法管理运行时状态

### 决策 2：Provider 模式实现跨模块访问

**选择**：通过 `PluginInstallationProvider` 协议实现依赖倒置

```python
# framework/tenant/plugin_protocols.py
class PluginInstallationProvider(Protocol):
    async def get_tenant_installations(self, tenant_id: str) -> list[PluginInstallationDTO]: ...
    async def create_installation(self, tenant_id: str, data: PluginInstallationDTO) -> PluginInstallationDTO: ...
    async def delete_installation(self, tenant_id: str, plugin_id: str) -> None: ...
```

**理由**：
- 避免AI → Tenant 的直接模块依赖
- Tenant 实现协议，AI 通过框架获取实例
- 使用独立事务，避免 Session 跨模块传递

**替代方案**：
- 直接导入 Tenant Service：违反模块边界
- Inner HTTP API：性能开销大，增加复杂度

### 决策 3：事件驱动保证一致性

**选择**：使用领域事件处理跨模块操作失败

```
安装失败流程：
AI 安装插件 → Tenant 创建记录 → AI 创建配置失败
                                          ↓
                              发布 PluginInstallationFailed 事件
                                          ↓
                              Tenant 监听器删除记录
```

**理由**：
- 无法使用分布式事务
- 事件驱动提供最终一致性
- 失败可追溯，便于排查

**事件定义**：
```python
@dataclass
class PluginInstallationFailed:
    tenant_id: str
    plugin_id: str
    installation_id: str
    error_message: str
    timestamp: datetime
```

### 决策 4：插件定义注册方式

**选择**：混合模式（启动扫描 + API 动态注册）

```python
# 启动时自动扫描
POST /tenant/admin/v1/plugin-definitions/scan

# API 动态注册
POST /tenant/admin/v1/plugin-definitions/upload  # 本地上传
POST /tenant/admin/v1/plugin-definitions/fetch   # 远程拉取
```

**理由**：
- 启动扫描：零配置，开箱即用
- API 注册：支持动态管理，灵活性高
- 两种方式互补，满足不同场景

**替代方案**：
- 仅启动扫描：无法动态添加
- 仅 API 注册：需要手动操作

### 决策 5：插件隔离策略

**选择**：默认使用 `shared` 模式，预留 `.venv` 和 `docker`

```python
POST /ai/console/v1/plugins/installations
Request: {
    "plugin_id": "langgenius/ollama",
    "install_type": "shared"  # 默认值
}
```

**理由**：
- `shared` 资源占用低，适合大多数场景
- 其他隔离方式实现复杂度高，后续按需开放

### 决策 6：统计数据获取方式

**选择**：实时计算 + 缓存（TTL 60s）

```python
# Tenant 统计
GET /tenant/admin/v1/plugin-definitions/statistics

# AI 统计
GET /ai/console/v1/plugins/statistics
```

**理由**：
- 统计数据不需要实时精确
- 缓存减少数据库压力
- TTL 60s 平衡性能和时效性

**替代方案**：
- 预计算统计表：增加复杂度，维护成本高
- 实时查询：大数据量时性能问题

## 风险 / 权衡

### 风险 1：数据不一致

**风险**：安装过程中 AI 侧创建失败，Tenant 侧记录已存在（孤儿记录）

**缓解措施**：
- 实现事件处理器立即回滚
- 添加定时任务清理孤儿记录
- 记录详细日志便于手动排查

### 风险 2：缓存一致性

**风险**：`PluginManager.plugins` 内存缓存与数据库不一致

**缓解措施**：
- 缓存 TTL = 60 秒
- 提供手动刷新接口
- 关键操作后主动失效缓存

### 风险 3：插件定义删除

**风险**：删除插件定义时，可能还有租户在使用

**缓解措施**：
- `refers > 0` 时禁止删除
- 提供"禁用"操作作为软删除
- 禁用后不影响已安装租户使用

### 风险 4：迁移过程服务中断

**风险**：从旧表迁移到新表期间，插件功能不可用

**缓解措施**：
- 采用三阶段迁移（新增 → 重构 → 清理）
- 每阶段独立可回滚
- 阶段间充分测试验证

## 迁移计划

### 阶段 P0：基础设施（新增代码）

**目标**：新增表和 Provider，不影响现有功能

**步骤**：
1. 新增 `framework/tenant/plugin_protocols.py`（DTO、Provider 协议）
2. 新增 `tenant/models/plugin_definition.py`（ORM 模型）
3. 新增 `tenant/services/plugin_provider.py`（Provider 实现）
4. 新增 `ai/models/plugin_config.py`、`plugin_runtime_state.py`
5. 新增 `framework/events/domain_events.py`（事件定义）
6. 新增 `tenant/listeners/handlers/plugin_handler.py`（事件处理器）
7. 应用入口注册 Provider

**验证**：
- 单元测试通过
- Provider 可正常注入

### 阶段 P1：代码替换（重构）

**目标**：重构 AI 模块使用 Provider

**步骤**：
1. 重构 `PluginManager._load_plugins_metadata_from_database()`
2. 重构 `PluginManager._save_plugin_installation_to_database()`
3. 重构 `PluginManagementService` 所有 ORM 查询
4. 实现事件驱动的安装/卸载流程
5. 新增 Tenant 管理侧 API（定义注册、管理、统计）
6. 新增 AI 使用侧 API（可用列表、配置、监控、统计）
7. 迁移数据：`ai.plugins` → `tenant.plugin_definitions`
8. 迁移数据：`ai.plugin_installations` → 分离到两个表

**验证**：
- 所有集成测试通过
- 现有功能不受影响

### 阶段 P2：清理（删除旧代码）

**目标**：删除旧表和旧代码

**步骤**：
1. 删除 `ai.plugins`、`ai.plugin_declarations`、`ai.plugin_installations` 表
2. 删除 `ai/models/plugin.py` 中已迁移的模型
3. 更新文档

**验证**：
- 全量测试通过
- 生产环境验证

## 开放问题

1. **插件定义版本管理**：是否支持同一插件的多个版本并存？
   - 当前设计：不支持，同一 plugin_id 只能有一个版本
   - 后续考虑：引入版本管理机制

2. **插件依赖管理**：插件之间是否存在依赖关系？
   - 当前设计：不考虑依赖
   - 后续考虑：声明依赖并自动安装

3. **插件市场集成**：是否对接第三方插件市场？
   - 当前设计：仅支持远程 URL 拉取
   - 后续考虑：对接 Dify 插件市场或其他平台
