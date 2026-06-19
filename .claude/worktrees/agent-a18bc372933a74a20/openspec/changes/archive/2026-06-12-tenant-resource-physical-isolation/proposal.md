## 为什么

当前租户资源管理器（TenantCacheManager、TenantStorageManager）仅支持**逻辑隔离**（同一实例的不同 DB/bucket），不支持**物理隔离**（不同实例）。随着已完成的数据模型重构，TenantCacheConfig、TenantQueueConfig、TenantPubSubConfig 已补全 host/port/password 等连接参数，但资源管理器层未使用这些参数连接独立实例。

这是架构层面的能力缺失，限制了需要独立 Redis/MinIO 实例的租户隔离场景。

## 变更内容

1. **TenantCacheManager 增强**：支持根据 TenantCacheConfig 的 host/port/password 连接不同的 Redis 实例
2. **TenantStorageManager 增强**：支持根据 TenantStorageConfig 的 endpoint/access_key/secret_key 连接不同的存储服务
3. **新增 TenantQueueManager**：管理租户级队列资源，支持 RabbitMQ/Kafka 等不同实例
4. **新增 TenantPubSubManager**：管理租户级发布订阅资源，支持 Redis/Kafka 等不同实例
5. **验证已有修改**：确保数据模型层重构完整，包括迁移脚本、缓存 L2 序列化、Schema 定义等

## 功能 (Capabilities)

### 新增功能

- `tenant-queue-manager`: 租户级队列管理器，支持连接不同队列实例（Redis Stream/RabbitMQ/Kafka）
- `tenant-pubsub-manager`: 租户级发布订阅管理器，支持连接不同消息实例（Redis PubSub/Kafka）

### 修改功能

- `tenant-cache-manager`: 扩展支持物理隔离，根据配置连接不同 Redis 实例（host/port/password）
- `tenant-storage-manager`: 扩展支持物理隔离，根据配置连接不同存储服务（endpoint/access_key/secret_key）
- `cache`: 增量规范，明确物理隔离场景下的缓存行为
- `queue`: 增量规范，明确租户队列物理隔离需求
- `pubsub`: 增量规范，明确租户发布订阅物理隔离需求

## 影响

### 受影响的代码

| 模块 | 文件 | 影响程度 |
|------|------|----------|
| framework/cache | `tenant_cache_manager.py` | 重大修改 |
| framework/storage | `tenant_storage_manager.py` | 重大修改 |
| framework/queue | 新增 `tenant_queue_manager.py` | 新增 |
| framework/pubsub | 新增 `tenant_pubsub_manager.py` | 新增 |
| framework/tenant | `protocols.py` | 已修改（补充字段） |
| framework/tenant | `cache.py` | 已修改（L2 序列化） |
| tenant/models | `tenant.py` | 已修改（删除内嵌字段） |
| tenant/migrations | `003_tenant_resource_ref.py` | 新增 |

### API 端点

- `/admin/v1/tenants` - 资源绑定接口已更新
- `/inner/v1/tenants` - 内部接口已更新，返回资源配置详情

### 兼容性

- **向后兼容**：不提供物理隔离配置时，行为与之前一致（使用默认实例）
- **迁移策略**：现有租户数据无需迁移，物理隔离为可选能力
