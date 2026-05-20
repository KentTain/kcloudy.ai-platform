## Why

当前系统缺少多租户支持，无法实现租户级别的数据隔离和资源管理。随着平台面向多组织部署的需求增加，需要实现一套完整的多租户框架，支持租户上下文管理、多资源数据隔离（数据库、Redis、MinIO）、租户缓存以及管理后台。

## What Changes

- 新增租户上下文管理（TenantContext），支持请求级别的租户信息存储与获取
- 新增租户中间件（TenantMiddleware），自动解析和注入租户上下文
- 新增数据库字段级隔离（TenantMixin + TenantEventListener），自动填充 tenant_id
- 新增 Redis 多资源隔离（缓存、队列、发布订阅、锁），自动注入租户前缀
- 新增 MinIO 存储隔离，自动拼接租户目录前缀
- 新增租户两级缓存（L1 本地内存 + L2 Redis）
- 新增异步任务租户上下文传递支持
- 新增租户管理后台 API（独立认证、跨租户管理）
- 新增默认租户管理员自动初始化
- 新增用户端租户 API（租户列表、当前租户、租户切换）
- **BREAKING**: 所有业务模型需继承 TenantMixin 以支持租户隔离

## Capabilities

### New Capabilities

- `tenant-context`: 租户上下文管理，包括 ContextVar 存储、租户信息获取与设置、请求结束后自动清理
- `tenant-middleware`: 租户中间件，从请求中解析租户标识、验证租户状态、加载租户信息并注入上下文
- `tenant-database-isolation`: 数据库字段级隔离，TenantMixin 模型混入、自动填充 tenant_id、查询自动过滤
- `tenant-redis-isolation`: Redis 多资源隔离，包括缓存 Key、队列 Stream、发布订阅 Channel、锁 Key 的自动前缀注入
- `tenant-storage-isolation`: MinIO 存储隔离，自动拼接租户目录前缀、预签名 URL 包含租户路径
- `tenant-cache`: 租户两级缓存策略，L1 本地内存 + L2 Redis，缓存失效通知与跨实例同步
- `tenant-async-task`: 异步任务租户上下文传递，任务入队自动记录 tenant_id、执行时自动恢复上下文
- `tenant-admin-api`: 租户管理后台 API，独立认证体系、跨租户查询与操作、租户 CRUD 与激活/停用
- `tenant-user-api`: 用户端租户 API，获取可用租户列表、当前租户信息、租户切换

### Modified Capabilities

无（此为新增模块，不修改现有规范）

## Impact

### 受影响组件

- **framework/tenant/**: 新增租户模块（models、context、middleware、service、resolver、enums）
- **framework/database/mixins/**: 已有 TenantMixin，需确认完整性
- **framework/database/events/**: 已有 TenantEventListener，需确认完整性
- **framework/cache/**: RedisUtil 需增加租户前缀自动注入能力
- **framework/queue/**: 任务队列需增加租户上下文传递支持
- **framework/storage/**: MinIO 存储需增加租户目录隔离支持

### 受影响 API 端点

- `/admin/v1/tenants`: 新增租户管理 API
- `/admin/v1/tenants/{id}/activate`: 新增租户激活 API
- `/admin/v1/tenants/{id}/deactivate`: 新增租户停用 API
- `/console/v1/tenants`: 新增用户端租户 API
- `/console/v1/tenants/current`: 新增当前租户信息 API
- `/console/v1/tenants/{id}/switch`: 新增租户切换 API

### 数据库变更

- 新增 `tenants` 表（租户基本信息）
- 新增 `tenant_configs` 表（租户配置）
- 新增 `tenant_admins` 表（租户管理员）
- 新增 `user_tenants` 表（用户-租户关联）
- 所有业务表需添加 `tenant_id` 字段（迁移脚本）

### 兼容性考虑

- 现有业务代码无需感知租户隔离细节，由框架层自动处理
- 管理后台独立路由前缀 `/admin/v1/`，不经过租户中间件
- 提供 `skip_tenant=True` 参数供管理员跨租户操作场景使用
