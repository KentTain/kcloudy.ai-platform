## ADDED Requirements

### Requirement: 存储服务级物理隔离

系统 SHALL 支持根据 TenantStorageConfig 连接不同的存储服务。

#### Scenario: 连接独立存储服务
- **WHEN** 租户配置了 endpoint="https://minio-tenant-a.example.com"
- **THEN** 系统创建到该存储服务的独立客户端
- **AND** 使用配置的 access_key/secret_key 进行认证

#### Scenario: 使用默认存储服务
- **WHEN** 租户未配置 endpoint 或 endpoint 为空
- **THEN** 使用默认 MinIO 客户端
- **AND** 根据 bucket 配置决定存储桶

### Requirement: 存储客户端缓存

系统 SHALL 缓存不同存储服务的客户端连接。

#### Scenario: 复用已缓存的存储客户端
- **WHEN** 请求连接 endpoint="https://minio-a.com" 且该客户端已存在
- **THEN** 返回缓存的客户端

#### Scenario: 创建新的存储客户端
- **WHEN** 请求连接 endpoint="https://minio-b.com" 且该客户端不存在
- **THEN** 使用配置创建新的 MinIO 客户端
- **AND** 将客户端缓存到 _instance_storages

### Requirement: 密钥安全处理

系统 SHALL 安全处理存储服务的访问密钥。

#### Scenario: 密钥解密
- **WHEN** 配置中的 secret_key 为加密存储
- **THEN** 在创建客户端前解密密钥
- **AND** 解密后的密钥不记录到日志

### Requirement: 文件路径隔离

系统 SHALL 自动构建正确的文件存储路径。

#### Scenario: 物理隔离路径
- **WHEN** 配置了独立 endpoint
- **THEN** 文件路径不添加租户前缀

#### Scenario: 逻辑隔离路径
- **WHEN** 使用默认存储服务且无独立 bucket
- **THEN** 文件路径添加 {tenant_id}/ 前缀

## MODIFIED Requirements

### Requirement: 存储桶路由管理

系统 SHALL 根据租户配置路由到独立存储桶或独立存储服务。

#### Scenario: 租户配置独立存储服务
- **WHEN** 租户配置了 endpoint="https://minio-tenant.example.com"
- **THEN** 使用独立存储服务
- **AND** 使用配置的 bucket 作为存储桶

#### Scenario: 租户配置独立存储桶
- **WHEN** 租户配置了 bucket="tenant-a-bucket" 且未配置 endpoint
- **THEN** 使用默认存储服务的该存储桶
- **AND** 不添加路径前缀

#### Scenario: 租户无独立存储配置
- **WHEN** 租户未配置 bucket 且未配置 endpoint
- **THEN** 使用默认存储桶
- **AND** 文件路径添加 {tenant_id}/ 前缀

### Requirement: 存储桶自动创建

系统 SHALL 在物理隔离场景下自动创建存储桶。

#### Scenario: 独立服务的存储桶创建
- **WHEN** 配置了独立 endpoint 且存储桶不存在
- **THEN** 自动创建存储桶
- **AND** 记录创建日志
