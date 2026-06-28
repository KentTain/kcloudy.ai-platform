# Framework 模块开发指南

本文件为 Claude Code 在 `src/framework/` 基础设施模块中工作时提供指导。

## 模块定位

Framework 是 Python 后端的底层基础设施模块，提供配置、缓存、数据库、存储、队列、发布订阅、分布式锁、多租户和通用工具能力。

## 依赖边界

```
demo / iam / ai ──▶ framework
framework ──X──▶ demo / iam / ai
```

- 业务模块可以依赖 framework
- framework 禁止依赖业务模块
- 如需业务能力，必须通过 Protocol、注册器或启动期注入实现依赖倒置

## 目录职责

| 目录 | 职责 |
|------|------|
| cache/ | Redis 工具、租户缓存管理 |
| clients/ | 内部 HTTP 客户端、IAM 客户端 |
| common/ | 通用上下文、异常、响应、枚举 |
| configs/ | YAML 配置加载、环境变量覆盖 |
| core/ | 存储队列发布订阅锁等 Protocol 抽象接口 |
| database/ | SQLAlchemy 基础模型、Mixin、引擎池 |
| lock/ | 分布式锁工厂与实现 |
| module/ | 模块动态加载系统、注册中心 |
| pubsub/ | 发布订阅工厂与 Redis 实现 |
| queue/ | 队列工厂、Redis Stream 实现 |
| schemas/ | Pydantic VO 基类 |
| storage/ | 对象存储工厂、MinIO/OSS 实现 |
| tenant/ | 租户模型、上下文、中间件 |
| utils/ | 加密、JWT、时间、树形结构等工具 |

## 核心组件

| 组件 | 用途 |
|------|------|
| TenantContext | 租户上下文管理（contextvars） |
| DatabaseEnginePool | 租户引擎池管理（LRU 缓存） |
| ModuleRegistry | 模块注册中心 |
| TenantCacheManager | 租户缓存管理器 |
| TenantStorageManager | 租户存储管理器 |

## 多租户资源隔离

| 资源 | 物理隔离 | 逻辑隔离 |
|------|---------|---------|
| 数据库 | 独立 Database / Schema | tenant_id 字段过滤 |
| 缓存 | 独立 Redis DB | Key 前缀 {tenant_id}:{key} |
| 存储 | 独立 Bucket | 路径前缀 {tenant_id}/{path} |
| 队列 | 独立 Stream Key | Key 前缀 {tenant_id}:queue:{name} |

### 物理隔离 vs 逻辑隔离

**物理隔离**：每个租户使用完全独立的资源实例。

- Redis：独立的 host/port，完全隔离的 Redis 服务
- MinIO：独立的 endpoint，完全隔离的存储服务
- 优势：数据安全性最高，资源可独立扩缩容
- 适用场景：企业级租户、合规要求高的场景

**逻辑隔离**：多个租户共享同一资源实例，通过命名区分。

- Redis：共享实例，通过 DB 编号（0-15）或 Key 前缀区分
- MinIO：共享服务，通过 Bucket 名称或路径前缀区分
- 优势：资源利用率高、运维成本低
- 适用场景：中小租户、开发测试环境

### 配置独立 Redis 实例

租户缓存配置通过 `TenantCacheConfig` 定义：

```python
from framework.tenant.protocols import TenantCacheConfig

# 物理隔离：独立 Redis 实例
config = TenantCacheConfig(
    host="redis-tenant-a.example.com",
    port=6379,
    password="secret",
    db=0,
)

# 逻辑隔离：独立 Redis DB
config = TenantCacheConfig(
    db=5,  # 使用 DB 5
)

# 逻辑隔离：Key 前缀（无需特殊配置，默认行为）
# Key 格式：{tenant_id}:{key}
```

使用 `TenantCacheManager` 操作：

```python
from framework.cache.tenant_cache_manager import get_cache_manager

cache = get_cache_manager()

# 物理隔离：传入完整配置
await cache.set("user:123", "data", config=tenant_config)

# 逻辑隔离：独立 DB
await cache.set("user:123", "data", config=TenantCacheConfig(db=5))

# 默认逻辑隔离：Key 前缀自动添加
# 实际 Key：tenant_001:user:123
await cache.set("user:123", "data", tenant_id="tenant_001")
```

### 配置独立存储服务

租户存储配置通过 `TenantStorageConfig` 定义：

```python
from framework.tenant.protocols import TenantStorageConfig

# 物理隔离：独立存储服务
config = TenantStorageConfig(
    endpoint="https://minio-tenant-a.example.com",
    access_key="tenant-a-key",
    secret_key="tenant-a-secret",
    bucket="data",
)

# 逻辑隔离：独立 Bucket
config = TenantStorageConfig(
    bucket="tenant-a-bucket",
)

# 逻辑隔离：路径前缀（无需特殊配置，默认行为）
# 路径格式：{tenant_id}/{path}
```

使用 `TenantStorageManager` 操作：

```python
from framework.storage.tenant_storage_manager import get_storage_manager

storage = get_storage_manager()

# 物理隔离：传入完整配置
await storage.upload("report.pdf", data, config=tenant_config)

# 逻辑隔离：独立 Bucket
await storage.upload("report.pdf", data, config=TenantStorageConfig(bucket="tenant-a"))

# 默认逻辑隔离：路径前缀自动添加
# 实际路径：tenant_001/report.pdf
await storage.upload("report.pdf", data, tenant_id="tenant_001")
```

### 使用 TenantQueueManager

租户队列管理器委托给 `TenantCacheManager` 进行 Redis Stream 操作：

```python
from framework.queue.tenant_queue_manager import get_queue_manager

queue = get_queue_manager()

# 物理隔离：独立 Redis 实例
from framework.tenant.protocols import TenantQueueConfig
queue_config = TenantQueueConfig(host="redis-tenant-a.example.com", port=6379)
await queue.xadd("orders", {"action": "create"}, config=queue_config)

# 逻辑隔离：队列名前缀自动添加
# 实际队列名：tenant_001:queue:orders
await queue.xadd("orders", {"action": "create"}, tenant_id="tenant_001")

# 消费消息
messages = await queue.xreadgroup(
    groupname="workers",
    consumername="worker-1",
    queue_name="orders",
    tenant_id="tenant_001",
)

# 确认消息
await queue.xack("orders", "workers", msg_id, tenant_id="tenant_001")
```

### 使用 TenantPubSubManager

租户发布订阅管理器委托给 `TenantCacheManager` 进行 Redis PubSub 操作：

```python
from framework.pubsub.tenant_pubsub_manager import get_pubsub_manager

pubsub = get_pubsub_manager()

# 物理隔离：独立 Redis 实例
from framework.tenant.protocols import TenantPubSubConfig
pubsub_config = TenantPubSubConfig(host="redis-tenant-a.example.com", port=6379)
await pubsub.publish("notifications", "message", config=pubsub_config)

# 逻辑隔离：频道名前缀自动添加
# 实际频道名：tenant_001:channel:notifications
await pubsub.publish("notifications", "message", tenant_id="tenant_001")

# 订阅频道
subscription = await pubsub.subscribe("notifications", tenant_id="tenant_001")
async for message in subscription.listen():
    if message["type"] == "message":
        print(message["data"])
```

### 配置来源

租户资源配置通常从租户信息中获取：

```python
from framework.tenant.protocols import get_tenant_provider

provider = get_tenant_provider()
tenant_info = await provider.get_tenant("tenant_001")

# 使用租户配置
if tenant_info.cache:
    await cache.set("key", "value", config=tenant_info.cache)
if tenant_info.storage:
    await storage.upload("file.pdf", data, config=tenant_info.storage)
```

## 开发规则

- 抽象能力优先定义在 `core/` 或 `tenant/protocols.py`
- 根据配置选择实现时使用工厂函数
- 数据库模型继承 framework 提供的基类和 Mixin
- Redis、存储、队列等外部资源访问应通过 framework 封装入口
- 敏感租户配置使用 AES-256-GCM 加密工具处理

## 测试

- 单元测试：`tests/framework/unit/`
- 集成测试：`tests/framework/integration/`（依赖 Redis、PostgreSQL、MinIO）

```bash
uv run pytest tests/framework/unit/ -v
uv run pytest tests/framework/integration/ -v
```

详细设计和使用示例见 [README.md](README.md)。

## 模块元数据声明

### 概述

模块元数据声明是一种声明式的方式，用于定义模块的菜单、权限、角色等元数据。系统启动时会自动将这些定义同步到数据库，确保代码与数据库状态一致。

### 实现步骤

在模块的 `module.py` 中实现 `get_module_definition()` 方法：

```python
from framework.module.definition import (
    MenuDef,
    ModuleDefinition,
    PermissionDef,
    RoleDef,
)

class MyModule:
    # ... 其他方法 ...

    def get_module_definition(self) -> ModuleDefinition:
        """
        返回模块的元数据定义
        """
        return ModuleDefinition(
            code="mymodule",
            name="我的模块",
            description="模块描述",
            icon="Apps",
            version="1.0.0",
            menus=[...],
            permissions=[...],
            default_roles=[...],
        )
```

### 数据结构

#### MenuDef（菜单定义）

```python
@dataclass
class MenuDef:
    code: str           # 唯一标识，格式：<module>.<name>
    name: str           # 显示名称
    path: str           # 前端路由路径
    icon: str | None    # 图标标识（可选）
    parent_code: str | None  # 父菜单 code（可选）
    sort_order: int     # 排序顺序，默认 0
    is_visible: bool    # 是否可见，默认 True
```

#### PermissionDef（权限定义）

```python
@dataclass
class PermissionDef:
    code: str           # 唯一标识，格式：<module>:<resource>:<action>
    name: str           # 显示名称
    resource: str       # 资源名称
    action: str         # 操作类型：read/write/delete
    description: str | None  # 权限描述（可选）
```

#### RoleDef（角色定义）

```python
@dataclass
class RoleDef:
    code: str           # 角色编码
    name: str           # 角色名称
    description: str | None  # 角色描述（可选）
    permission_codes: list[str]  # 关联的权限 code 列表
    is_system: bool     # 是否系统内置角色，默认 False
```

#### ModuleDefinition（模块定义）

```python
@dataclass
class ModuleDefinition:
    code: str           # 模块编码
    name: str           # 模块名称
    description: str | None  # 模块描述（可选）
    icon: str | None    # 图标标识（可选）
    version: str        # 模块版本，默认 "1.0.0"
    menus: list[MenuDef]
    permissions: list[PermissionDef]
    default_roles: list[RoleDef]
```

### 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 菜单 code | `<module>.<name>` | `iam.users`, `demo.home` |
| 权限 code | `<module>:<resource>:<action>` | `iam:user:read`, `demo:dataset:write` |

**权限通配符**：角色可以引用通配符权限，如 `iam:*:read` 匹配模块所有读取权限。

### 完整示例

参考 IAM 模块的实现（`src/iam/module.py`）：

```python
def get_module_definition(self) -> ModuleDefinition:
    return ModuleDefinition(
        code="iam",
        name="系统管理",
        description="用户认证、授权、角色权限管理",
        icon="Shield",
        version="1.0.0",
        menus=[
            MenuDef(code="iam.users", name="用户管理", path="/iam/users", icon="Users", sort_order=1),
            MenuDef(code="iam.roles", name="角色管理", path="/iam/roles", icon="Badge", sort_order=2),
            MenuDef(code="iam.organizations", name="组织管理", path="/iam/organizations", icon="Building", sort_order=3),
        ],
        permissions=[
            PermissionDef(code="iam:user:read", name="查看用户", resource="user", action="read"),
            PermissionDef(code="iam:user:write", name="编辑用户", resource="user", action="write"),
            PermissionDef(code="iam:user:delete", name="删除用户", resource="user", action="delete"),
            # ... 更多权限
        ],
        default_roles=[
            RoleDef(
                code="admin",
                name="管理员",
                description="IAM 模块管理员，拥有所有权限",
                permission_codes=["iam:*:*"],
                is_system=True,
            ),
            RoleDef(
                code="viewer",
                name="查看者",
                description="IAM 模块只读用户",
                permission_codes=["iam:*:read"],
                is_system=True,
            ),
        ],
    )
```

### 同步机制

系统启动时，`ModuleDefinitionSyncService` 会：

1. **Upsert 模块记录**：创建或更新 `Module` 表中的模块信息
2. **同步菜单**：创建或更新菜单，处理父子关系
3. **同步权限**：创建或更新权限定义
4. **同步角色**：创建或更新角色，关联权限
5. **清理孤儿数据**：删除数据库中已不存在于模块定义的菜单、权限、角色

### 注意事项

1. **菜单层级**：支持多级菜单，通过 `parent_code` 建立父子关系
2. **循环引用检测**：系统会自动检测菜单的循环引用并报错
3. **权限引用验证**：角色引用的权限必须存在于同一模块的权限列表中
4. **幂等性**：多次执行同步操作是安全的，不会产生重复数据
