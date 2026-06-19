# 默认资源配置初始化提案

## 为什么

当前租户模块缺少默认资源配置的初始化机制。创建租户时，如果没有指定资源配置，系统无法自动关联默认配置。这导致：
1. 运维人员需要手动创建资源配置后才能创建租户
2. 每个租户都需要手动关联配置，操作繁琐
3. 缺少配置管理规范，容易产生配置混乱

通过引入默认资源配置初始化机制，可以实现：
- 应用启动时自动创建默认资源配置
- 创建租户时自动关联默认配置（如果未指定）
- 支持租户级资源隔离（默认共享，支持独立配置）

## 变更内容

### 新增功能

1. **资源配置模型增强**
   - 为 `DatabaseConfig`、`CacheConfig`、`StorageConfig`、`QueueConfig`、`PubSubConfig` 模型添加 `is_default` 字段
   - 添加数据库部分唯一索引，确保每种配置类型只有一个默认配置

2. **默认配置种子数据**
   - 新增 `resource_config_seed.py` 种子脚本
   - 启动时从 `application.yml` 读取配置并创建默认资源配置
   - 使用 AES-256-GCM 加密敏感字段（密码、密钥等）

3. **租户创建自动关联**
   - 创建租户时，如果未传入资源配置 ID，自动关联默认配置
   - 查询资源配置列表时，`is_default=True` 的配置排在第一位

4. **前端资源配置选择**
   - 创建租户页面显示资源配置选择器
   - 默认配置自动排在第一位且默认选中

### 修改功能

- 修改 `TenantService.create()` 方法，支持自动填充默认配置
- 修改资源配置服务层，支持 `is_default` 字段的唯一性控制
- 修改资源配置查询接口，按 `is_default` 降序排序

## 功能 (Capabilities)

### 新增功能

- `default-resource-config`: 默认资源配置管理功能，包括配置初始化、默认标记、自动关联

### 修改功能

- `tenant-management`: 租户管理功能需求变更，创建租户时支持自动关联默认资源配置

## 影响

### 后端影响

**模型层**：
- `tenant/models/database_config.py` - 新增 `is_default` 字段
- `tenant/models/cache_config.py` - 新增 `is_default` 字段
- `tenant/models/storage_config.py` - 新增 `is_default` 字段
- `tenant/models/queue_config.py` - 新增 `is_default` 字段
- `tenant/models/pubsub_config.py` - 新增 `is_default` 字段

**服务层**：
- `tenant/services/tenant_service.py` - 修改 `create()` 方法，支持自动填充默认配置
- `tenant/services/database_config_service.py` - 新增 `is_default` 唯一性控制
- `tenant/services/cache_config_service.py` - 新增 `is_default` 唯一性控制
- `tenant/services/storage_config_service.py` - 新增 `is_default` 唯一性控制
- `tenant/services/queue_config_service.py` - 新增 `is_default` 唯一性控制
- `tenant/services/pubsub_config_service.py` - 新增 `is_default` 唯一性控制

**控制器层**：
- `tenant/controllers/admin/resource_config_controller.py` - 修改查询接口，支持 `is_default` 排序

**种子数据**：
- `tenant/migrations/seeds/resource_config_seed.py` - 新增默认资源配置种子脚本
- `tenant/migrations/seeds/tenant_seed.py` - 修改默认租户创建逻辑，关联默认配置

**数据库迁移**：
- 新增迁移脚本，添加 `is_default` 字段和部分唯一索引

**Schema**：
- `tenant/schemas/admin/resource_config.py` - 响应模型新增 `is_default` 字段

### 前端影响

**类型定义**：
- `web/vue/src/tenant/types/resource.ts` - 新增 `is_default` 字段

**页面组件**：
- `web/vue/src/tenant/pages/tenants/TenantCreate.vue` - 新增资源配置选择器

### API 影响

**新增响应字段**：
- `GET /tenant/admin/v1/database-configs` - 响应新增 `is_default` 字段
- `GET /tenant/admin/v1/cache-configs` - 响应新增 `is_default` 字段
- `GET /tenant/admin/v1/storage-configs` - 响应新增 `is_default` 字段
- `GET /tenant/admin/v1/queue-configs` - 响应新增 `is_default` 字段
- `GET /tenant/admin/v1/pubsub-configs` - 响应新增 `is_default` 字段

**行为变更**：
- `POST /tenant/admin/v1/tenants` - 未传入资源配置 ID 时自动使用默认配置

### 数据库影响

**新增字段**：
- `tenant.database_configs.is_default`
- `tenant.cache_configs.is_default`
- `tenant.storage_configs.is_default`
- `tenant.queue_configs.is_default`
- `tenant.pubsub_configs.is_default`

**新增索引**：
- `uix_database_configs_default` - 部分唯一索引（WHERE is_default = TRUE）
- `uix_cache_configs_default` - 部分唯一索引
- `uix_storage_configs_default` - 部分唯一索引
- `uix_queue_configs_default` - 部分唯一索引
- `uix_pubsub_configs_default` - 部分唯一索引

### 兼容性

**向后兼容**：
- 现有租户不受影响（`db_config_id` 等字段已存在）
- 现有 API 签名不变（仅响应新增字段）
- 新增字段有默认值（`is_default=False`）

**迁移策略**：
1. 新增 `is_default` 字段（默认 `False`，非空）
2. 创建部分唯一索引
3. 种子数据初始化默认配置
4. 现有租户可手动关联配置或保持原状
