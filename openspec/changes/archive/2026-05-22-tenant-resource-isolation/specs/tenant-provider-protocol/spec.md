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
