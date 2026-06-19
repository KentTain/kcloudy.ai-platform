## ADDED Requirements

### Requirement: TenantProvider 协议定义

系统 SHALL 定义 `TenantProvider` Protocol，抽象租户获取逻辑，支持本地部署和分布式部署。

#### Scenario: 本地部署获取租户

- **WHEN** 应用部署为单体架构
- **THEN** TenantProvider 实现直接访问数据库获取租户信息

#### Scenario: 分布式部署获取租户

- **WHEN** 应用部署为微服务架构，IAM 服务独立部署
- **THEN** TenantProvider 实现通过 RPC/HTTP 调用 IAM 服务获取租户信息

### Requirement: TenantInfo 协议定义

系统 SHALL 定义 `TenantInfo` Protocol，作为租户信息的标准接口。

#### Scenario: 获取租户基础信息

- **WHEN** 调用 TenantInfo 的属性
- **THEN** 可获取 id、name、code、status 等基础信息

#### Scenario: 获取租户资源配置

- **WHEN** 租户配置了独立的数据库、存储、队列资源
- **THEN** 可通过 database、storage、queue、pubsub 属性获取配置

### Requirement: 资源配置数据结构

系统 SHALL 定义租户资源配置的 dataclass：`TenantDatabaseConfig`、`TenantStorageConfig`、`TenantQueueConfig`、`TenantPubSubConfig`。

#### Scenario: 数据库配置默认值

- **WHEN** 创建 TenantDatabaseConfig 实例不传参数
- **THEN** 默认 type 为 POSTGRESQL，port 为 5432

#### Scenario: 存储配置默认值

- **WHEN** 创建 TenantStorageConfig 实例不传参数
- **THEN** 默认 type 为 MINIO

### Requirement: TenantProvider 全局注册

系统 SHALL 提供全局注册机制：`register_tenant_provider()` 和 `get_tenant_provider()`。

#### Scenario: 启动时注册

- **WHEN** 应用启动时调用 `register_tenant_provider(provider)`
- **THEN** 后续调用 `get_tenant_provider()` 返回注册的实例

#### Scenario: 未注册时访问

- **WHEN** 未调用 `register_tenant_provider()` 时调用 `get_tenant_provider()`
- **THEN** 抛出 RuntimeError，提示需要注册

### Requirement: SimpleTenant 实现 TenantInfo

`SimpleTenant` dataclass SHALL 实现 `TenantInfo` Protocol。

#### Scenario: 从 ORM 模型创建

- **WHEN** 调用 `SimpleTenant.from_model(orm_tenant)`
- **THEN** 返回包含 id、name、code、status 的 SimpleTenant 实例

#### Scenario: 可选资源配置

- **WHEN** 创建 SimpleTenant 不传资源配置
- **THEN** database、storage、queue、pubsub 属性为 None

### Requirement: TenantProvider 方法

`TenantProvider` Protocol SHALL 定义以下方法：

- `get_tenant(tenant_id: str) -> TenantInfo | None`
- `validate_access(user_id: str, tenant_id: str) -> bool`
- `get_user_tenants(user_id: str) -> list[TenantInfo]`

#### Scenario: 获取存在的租户

- **WHEN** 调用 `get_tenant("existing_tenant_id")`
- **THEN** 返回对应的 TenantInfo

#### Scenario: 获取不存在的租户

- **WHEN** 调用 `get_tenant("nonexistent_id")`
- **THEN** 返回 None

#### Scenario: 验证用户有权访问租户

- **WHEN** 用户属于该租户，调用 `validate_access(user_id, tenant_id)`
- **THEN** 返回 True

#### Scenario: 验证用户无权访问租户

- **WHEN** 用户不属于该租户，调用 `validate_access(user_id, tenant_id)`
- **THEN** 返回 False

#### Scenario: 获取用户所属租户列表

- **WHEN** 调用 `get_user_tenants(user_id)`
- **THEN** 返回用户所属的所有租户列表

### Requirement: framework 模块依赖规则

framework 模块 SHALL NOT 引用业务模块（demo、iam）。

#### Scenario: 中间件获取租户信息

- **WHEN** TenantMiddleware 需要获取租户信息
- **THEN** 通过 `get_tenant_provider()` 获取 Provider，不直接依赖 iam 模块

#### Scenario: 任务执行器恢复租户上下文

- **WHEN** TenantTaskExecutor 需要恢复租户上下文
- **THEN** 通过 `get_tenant_provider()` 获取 Provider，不直接依赖 iam 模块

## ADDED Requirements

### Requirement: TenantInfo 协议扩展

系统 SHALL 扩展 TenantInfo 协议，包含完整的资源配置信息。

#### Scenario: TenantInfo 包含数据库配置
- **WHEN** 获取 TenantInfo
- **THEN** 可访问 database 属性返回 TenantDatabaseConfig
- **AND** 未配置时返回 None

#### Scenario: TenantInfo 包含存储配置
- **WHEN** 获取 TenantInfo
- **THEN** 可访问 storage 属性返回 TenantStorageConfig
- **AND** 未配置时返回 None

#### Scenario: TenantInfo 包含缓存配置
- **WHEN** 获取 TenantInfo
- **THEN** 可访问 cache 属性返回 TenantCacheConfig
- **AND** 未配置时返回 None

### Requirement: TenantDatabaseConfig 数据类

系统 SHALL 提供 TenantDatabaseConfig 数据类封装数据库连接配置。

#### Scenario: TenantDatabaseConfig 包含完整连接参数
- **WHEN** 创建 TenantDatabaseConfig
- **THEN** 包含 type、host、port、database、username、password 属性
- **AND** 密码字段已解密

### Requirement: TenantStorageConfig 数据类

系统 SHALL 提供 TenantStorageConfig 数据类封装存储配置。

#### Scenario: TenantStorageConfig 包含存储桶信息
- **WHEN** 创建 TenantStorageConfig
- **THEN** 包含 type、bucket 属性

### Requirement: TenantCacheConfig 数据类

系统 SHALL 提供 TenantCacheConfig 数据类封装缓存配置。

#### Scenario: TenantCacheConfig 包含 DB 编号
- **WHEN** 创建 TenantCacheConfig
- **THEN** 包含 db 属性（Redis DB 编号）

### Requirement: TenantProvider 扩展

系统 SHALL 扩展 TenantProvider 协议，支持返回完整资源配置。

#### Scenario: TenantProvider 返回完整租户信息
- **WHEN** 调用 TenantProvider.get_tenant(tenant_id)
- **THEN** 返回包含完整资源配置的 TenantInfo
- **AND** 敏感字段（如密码）已解密
