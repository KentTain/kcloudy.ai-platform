## Why

当前系统仅实现了租户级逻辑隔离（字段过滤、Key 前缀、路径前缀），无法满足高安全要求租户的数据隔离需求。物理隔离可为不同租户提供独立的数据库、存储桶和缓存空间，彻底杜绝跨租户数据泄露风险。

## What Changes

- **IAM 模块 - Tenant 模型扩展**
  - 新增数据库资源配置字段：`db_type`、`db_host`、`db_port`、`db_name`、`db_username`、`db_password`（加密存储）
  - 新增存储资源配置字段：`storage_type`、`storage_bucket`
  - 新增缓存资源配置字段：`cache_db`（Redis DB 编号 0-15）
  - 新增加密密钥字段：`encryption_key`（用于敏感信息加密）
  - 新增数据库迁移脚本

- **Framework 模块 - 资源连接管理**
  - 新增 `DatabaseEnginePool`：数据库连接池缓存管理器，支持惰性加载 + LRU 回收
  - 新增 `TenantStorageManager`：存储 Bucket 路由管理器
  - 新增 `TenantCacheManager`：Redis DB 路由管理器
  - 更新 `TenantContext`：支持访问租户资源配置

- **平滑迁移支持**
  - 未配置独立资源的租户继续使用逻辑隔离（兼容现有行为）
  - 新租户可选择启用物理隔离

## Capabilities

### New Capabilities

- `tenant-resource-config`: 租户资源配置能力，包括数据库、存储、缓存资源的配置管理和加密存储
- `database-engine-pool`: 数据库连接池缓存管理，支持按租户动态创建和回收连接池
- `tenant-storage-manager`: 租户存储管理器，支持按租户配置路由到独立 Bucket
- `tenant-cache-manager`: 租户缓存管理器，支持按租户配置路由到独立 Redis DB

### Modified Capabilities

- `tenant-database-isolation`: 扩展支持物理隔离模式（独立 Database），未配置时继续使用逻辑隔离
- `tenant-storage-isolation`: 扩展支持物理隔离模式（独立 Bucket），未配置时继续使用逻辑隔离
- `tenant-redis-isolation`: 扩展支持物理隔离模式（独立 Redis DB），未配置时继续使用逻辑隔离
- `tenant-provider-protocol`: 更新 `TenantInfo` 协议，包含完整的资源配置信息

## Impact

### 受影响的代码模块

- `server/python/src/iam/models/tenant.py` - Tenant 模型扩展
- `server/python/src/iam/services/tenant_service.py` - 租户服务更新
- `server/python/src/iam/services/tenant_provider_impl.py` - TenantProvider 实现更新
- `server/python/src/framework/tenant/protocols.py` - 协议定义扩展
- `server/python/src/framework/tenant/context.py` - 上下文扩展
- `server/python/src/framework/database/core/engine.py` - 连接池缓存管理
- `server/python/src/framework/storage/` - 存储管理器
- `server/python/src/framework/cache/` - 缓存管理器

### 数据库迁移

- 新增迁移脚本：`20260522_001_add_tenant_resource_config.py`
- 迁移策略：所有新字段允许为空，确保现有租户数据兼容

### API 变更

- `/admin/v1/tenants` - 租户 CRUD 扩展资源配置字段
- 无破坏性变更，所有新字段可选
