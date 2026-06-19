## Why

当前 `framework/tenant` 模块存在架构问题：

1. **重复设计**：`framework/tenant/models.py` 中的 `Tenant` dataclass 与 `iam/models/tenant.py` 中的 ORM 模型概念重复，且前者未被使用
2. **架构违规**：`framework` 作为底层模块，违规引用了业务模块 `iam`（middleware.py、task_executor.py）
3. **扩展性不足**：缺乏服务抽象，无法支持分布式部署场景

此变更通过依赖倒置原则重构租户模块架构，解耦 framework 与业务模块，为未来的分布式部署做准备。

## What Changes

### 删除

- **`framework/tenant/models.py`**：未使用的 Tenant dataclass 及相关配置类

### 新增

- **`framework/tenant/protocols.py`**：协议定义
  - `TenantDatabaseConfig`、`TenantStorageConfig`、`TenantQueueConfig`、`TenantPubSubConfig`：资源配置 dataclass
  - `TenantInfo` Protocol：租户信息协议（扩展为包含资源配置）
  - `TenantProvider` Protocol：租户提供者协议（服务抽象）
  - `register_tenant_provider()` / `get_tenant_provider()`：全局注册机制
- **`iam/services/tenant_provider_impl.py`**：IAM 模块的 TenantProvider 实现

### 修改

- **`framework/tenant/context.py`**：`SimpleTenant` 实现 `TenantInfo` Protocol，添加资源配置字段
- **`framework/tenant/middleware.py`**：使用 `TenantProvider` 替代直接依赖 iam 模块
- **`framework/queue/task_executor.py`**：使用 `TenantProvider` 替代直接依赖 iam 模块
- **`framework/tenant/__init__.py`**：更新模块导出
- **`application_web.py`**：应用启动时注册 `TenantProvider`
- **`framework/CLAUDE.md`**：添加模块依赖规则约束

## Capabilities

### New Capabilities

- `tenant-provider-protocol`：租户提供者协议，抽象租户获取逻辑，支持本地部署和分布式部署

### Modified Capabilities

无。此变更仅涉及实现层面的重构，不改变外部行为和 API 契约。

## Impact

### 受影响的代码

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `framework/tenant/models.py` | 删除 | 整合到 protocols.py |
| `framework/tenant/protocols.py` | 新增 | 协议定义 |
| `framework/tenant/context.py` | 修改 | SimpleTenant 扩展 |
| `framework/tenant/middleware.py` | 修改 | 使用 TenantProvider |
| `framework/tenant/__init__.py` | 修改 | 更新导出 |
| `framework/queue/task_executor.py` | 修改 | 使用 TenantProvider |
| `iam/services/tenant_provider_impl.py` | 新增 | TenantProvider 实现 |
| `application_web.py` | 修改 | 注册 TenantProvider |

### 受影响的 API

无。此变更不改变任何外部 API 行为。

### 依赖关系

```
变更前（违规）：
framework/tenant/middleware.py ──依赖──► iam/models/Tenant
framework/queue/task_executor.py ──依赖──► iam/services/TenantService

变更后（正确）：
framework/tenant/protocols.py ◄──实现── iam/services/tenant_provider_impl.py
```

### 迁移策略

1. 先创建 `protocols.py`，定义协议
2. 修改 `context.py`，扩展 SimpleTenant
3. 创建 `iam/services/tenant_provider_impl.py`，实现协议
4. 修改 `middleware.py` 和 `task_executor.py`，使用 TenantProvider
5. 修改 `application_web.py`，注册 TenantProvider
6. 删除 `models.py`
7. 更新 `__init__.py` 和 `CLAUDE.md`

### 兼容性考虑

- **内部兼容**：此变更影响内部模块间的依赖关系，但不影响外部 API
- **部署兼容**：现有部署无需修改，TenantProvider 默认使用本地实现
