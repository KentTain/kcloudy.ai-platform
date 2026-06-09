## MODIFIED Requirements

### Requirement: 租户模型定义
系统 SHALL 定义 Tenant 模型，包含数据库、存储、缓存、队列、发布订阅等资源配置字段，并通过 FK 关联独立的资源配置实体。

#### Scenario: 租户数据库配置
- **WHEN** 查询租户的数据库配置
- **THEN** 返回 `db_config_id` 关联的 DatabaseConfig 信息

#### Scenario: 租户存储配置
- **WHEN** 查询租户的存储配置
- **THEN** 返回 `storage_config_id` 关联的 StorageConfig 信息

#### Scenario: 租户缓存配置
- **WHEN** 查询租户的缓存配置
- **THEN** 返回 `cache_config_id` 关联的 CacheConfig 信息

#### Scenario: 租户队列配置
- **WHEN** 查询租户的队列配置
- **THEN** 返回 `queue_config_id` 关联的 QueueConfig 信息

#### Scenario: 租户发布订阅配置
- **WHEN** 查询租户的发布订阅配置
- **THEN** 返回 `pubsub_config_id` 关联的 PubSubConfig 信息

## ADDED Requirements

### 需求:租户业务配置

系统必须支持租户业务配置（TenantConfig），包含用户数限制、存储空间限制、API 调用次数限制等。

#### 场景:创建租户自动创建配置
- **当** 创建新租户
- **那么** 自动创建 TenantConfig 记录，默认值：max_users=100、max_storage_mb=1024、max_api_calls=10000

#### 场景:查询租户配置
- **当** 查询租户的业务配置
- **那么** 返回 TenantConfig 信息

#### 场景:更新租户配置
- **当** 管理员更新租户业务配置
- **那么** 更新 TenantConfig 记录
