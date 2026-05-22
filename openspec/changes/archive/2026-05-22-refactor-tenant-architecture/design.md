## Context

### 当前状态

`framework/tenant` 模块存在以下架构问题：

1. **重复设计**：`framework/tenant/models.py` 定义了 `Tenant` dataclass，但实际使用的是 `iam/models/tenant.py` 中的 ORM 模型
2. **架构违规**：`framework/tenant/middleware.py` 和 `framework/queue/task_executor.py` 直接依赖 `iam` 模块
3. **扩展性不足**：缺乏服务抽象层，无法支持模块分开部署的场景

### 约束条件

- framework 是底层基础设施模块，**禁止引用业务模块**（demo、iam）
- 必须保持现有 API 行为不变
- 必须支持本地部署和未来的分布式部署

### 利益相关者

- 后端开发团队：需要理解新的模块依赖规则
- 运维团队：未来分布式部署时需要配置 TenantProvider 的 RPC 实现

## Goals / Non-Goals

**Goals:**

- 解耦 framework 与 iam 模块，消除违规依赖
- 定义 `TenantProvider` Protocol，支持依赖倒置
- 扩展 `TenantInfo` Protocol，支持租户级资源配置
- 为分布式部署预留扩展点

**Non-Goals:**

- 不改变外部 API 行为
- 不实现分布式部署的 RPC Provider（仅预留接口）
- 不实现租户级资源隔离功能（仅定义数据结构）

## Decisions

### Decision 1：依赖倒置方案

**选择：定义 TenantProvider Protocol**

```
变更前（违规）：
framework/tenant/middleware.py ──依赖──► iam/models/Tenant
framework/queue/task_executor.py ──依赖──► iam/services/TenantService

变更后（正确）：
framework/tenant/protocols.py ◄──实现── iam/services/tenant_provider_impl.py
```

**理由：**
- 遵循依赖倒置原则（DIP），高层模块不依赖低层模块，两者都依赖抽象
- Protocol 是 Python 原生支持的接口定义方式，无需额外依赖
- 运行时注入实现，灵活支持本地部署和分布式部署

**备选方案：**

| 方案 | 优点 | 缺点 |
|------|------|------|
| Protocol（已选） | 原生支持、类型安全、无额外依赖 | 需要手动注册 |
| ABC 抽象类 | 更严格的约束 | 需要继承，不够灵活 |
| 回调函数 | 简单直接 | 类型不够明确 |

### Decision 2：全局注册 vs 依赖注入容器

**选择：全局注册（简单方案）**

```python
_tenant_provider: TenantProvider | None = None

def register_tenant_provider(provider: TenantProvider) -> None:
    global _tenant_provider
    _tenant_provider = provider

def get_tenant_provider() -> TenantProvider:
    if _tenant_provider is None:
        raise RuntimeError("TenantProvider not registered")
    return _tenant_provider
```

**理由：**
- 与项目现有风格一致（如 `RedisUtil`）
- 无需引入额外的 DI 框架
- 对于单体应用足够使用

**备选方案：**

| 方案 | 优点 | 缺点 |
|------|------|------|
| 全局注册（已选） | 简单、与现有风格一致 | 全局状态、测试时需要 mock |
| DI 容器 | 更灵活、易于测试 | 需要引入框架、增加复杂度 |

### Decision 3：资源配置的位置

**选择：放入 `framework/tenant/protocols.py`**

```python
@dataclass
class TenantDatabaseConfig:
    type: DatabaseType = DatabaseType.POSTGRESQL
    host: str = ""
    port: int = 5432
    ...

class TenantInfo(Protocol):
    @property
    def database(self) -> TenantDatabaseConfig | None: ...
```

**理由：**
- 资源配置是协议的一部分，放在一起便于理解
- 避免创建过多小文件
- 与 `TenantInfo` 紧密相关

### Decision 4：SimpleTenant 扩展方式

**选择：SimpleTenant 实现 TenantInfo Protocol**

```python
@dataclass
class SimpleTenant:
    id: str
    name: str
    code: str
    status: str = "active"
    # 新增
    database: TenantDatabaseConfig | None = None
    storage: TenantStorageConfig | None = None
    queue: TenantQueueConfig | None = None
    pubsub: TenantPubSubConfig | None = None
```

**理由：**
- dataclass 实现 Protocol 不需要显式继承
- 保持单一数据类用于上下文存储
- 可选字段保持向后兼容

## Risks / Trade-offs

### Risk 1：运行时未注册 TenantProvider

**风险：** 如果应用启动时未调用 `register_tenant_provider()`，运行时会抛出 `RuntimeError`

**缓解：**
- 在 `application_web.py` 的启动流程中尽早注册
- 文档中明确说明注册要求
- 考虑在开发模式下提供警告而非错误

### Risk 2：分布式部署时的网络延迟

**风险：** 未来分布式部署时，RPC 调用 IAM 服务获取租户信息会增加延迟

**缓解：**
- 两级缓存（L1 本地 + L2 Redis）减少 RPC 调用
- TenantProvider 实现可以包含本地缓存逻辑

### Trade-off：全局状态

**取舍：** 使用全局注册引入了全局状态

**理由：**
- 对于单体应用，全局状态是可接受的
- 未来如果需要，可以迁移到 DI 容器
- 全局状态使得测试时需要手动 mock，但这是可控的

## Migration Plan

### 阶段 1：创建新结构（无破坏性变更）

1. 创建 `framework/tenant/protocols.py`
2. 修改 `framework/tenant/context.py`，扩展 SimpleTenant
3. 创建 `iam/services/tenant_provider_impl.py`

### 阶段 2：切换依赖

4. 修改 `framework/tenant/middleware.py`，使用 TenantProvider
5. 修改 `framework/queue/task_executor.py`，使用 TenantProvider
6. 修改 `application_web.py`，注册 TenantProvider

### 阶段 3：清理

7. 删除 `framework/tenant/models.py`
8. 更新 `framework/tenant/__init__.py`
9. 更新 `framework/CLAUDE.md`

### 回滚策略

如果发现问题，可以：
1. 回滚 `middleware.py` 和 `task_executor.py` 的修改
2. 删除 `protocols.py` 和 `tenant_provider_impl.py`
3. 恢复 `models.py`

由于不涉及数据库变更，回滚风险很低。
