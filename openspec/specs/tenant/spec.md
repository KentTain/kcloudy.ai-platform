## ADDED Requirements

### Requirement: 租户模型定义
系统 SHALL 定义 Tenant 模型，包含数据库、存储、缓存、队列、发布订阅等资源配置字段。

#### Scenario: 租户数据库配置
- **WHEN** 查询租户的数据库配置
- **THEN** 返回 `database_type`、`server`、`database`、`connection_string` 等信息

#### Scenario: 租户存储配置
- **WHEN** 查询租户的存储配置
- **THEN** 返回 `storage_type`、`endpoint`、`access_key` 等信息

### Requirement: 租户资源类型枚举
系统 SHALL 定义租户资源类型枚举，包括 DatabaseType、StorageType、QueueType、PubSubType 等。

#### Scenario: 数据库类型枚举
- **WHEN** 使用 `DatabaseType.POSTGRESQL`
- **THEN** 表示 PostgreSQL 数据库类型

#### Scenario: 存储类型枚举
- **WHEN** 使用 `StorageType.MINIO`
- **THEN** 表示 MinIO 对象存储类型

### Requirement: 租户设置扩展
系统 SHALL 支持租户自定义设置，通过 key-value 形式存储。

#### Scenario: 存储租户设置
- **WHEN** 添加 `TenantSetting(name="theme", value="dark")`
- **THEN** 租户设置被保存

#### Scenario: 查询租户设置
- **WHEN** 查询租户的 `theme` 设置
- **THEN** 返回 `"dark"`

### Requirement: 租户上下文
系统 SHALL 提供租户上下文管理，支持在请求中获取当前租户。

#### Scenario: 设置当前租户
- **WHEN** 调用 `TenantContext.set_current_tenant(tenant)`
- **THEN** 后续可通过 `TenantContext.get_current_tenant()` 获取租户

#### Scenario: 清理租户上下文
- **WHEN** 请求结束
- **THEN** 租户上下文自动清理

### Requirement: 租户隔离级别
系统 SHALL 采用数据库级隔离，每个租户使用独立的数据库。

#### Scenario: 租户数据库隔离
- **WHEN** 租户 A 访问系统
- **THEN** 数据操作只涉及租户 A 的专属数据库

**注意**: 本模块仅包含模型设计，不涉及具体实现逻辑。
