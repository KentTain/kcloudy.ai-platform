## 上下文

### 当前状态

已完成数据模型层重构：
- Tenant 模型删除了内嵌配置字段（db_type, db_host 等），保留关联配置 ID
- TenantCacheConfig/TenantQueueConfig/TenantPubSubConfig 已补全连接参数
- 数据库迁移脚本已创建（003_tenant_resource_ref.py）
- 缓存 L2 序列化已支持完整资源配置

### 问题

资源管理器层未使用完整配置：
- `TenantCacheManager.get_client()` 仅使用 `config.db`，忽略 `host/port/password`
- `TenantStorageManager` 仅使用 `config.bucket`，忽略 `endpoint/access_key/secret_key`
- 不存在 `TenantQueueManager` 和 `TenantPubSubManager`

### 约束

1. 向后兼容：不提供物理隔离配置时，行为与之前一致
2. 客户端缓存：避免为每个请求创建新连接
3. 连接池管理：支持 LRU 淘汰空闲连接
4. 密码安全：配置中的密码已加密存储，使用时需解密

## 目标 / 非目标

**目标：**

1. TenantCacheManager 支持连接不同 Redis 实例
2. TenantStorageManager 支持连接不同存储服务
3. 新增 TenantQueueManager 管理队列资源
4. 新增 TenantPubSubManager 管理发布订阅资源
5. 验证已有数据模型修改的完整性

**非目标：**

1. 不修改前端代码（资源配置管理 UI 已完成）
2. 不实现数据库的物理隔离（已有 DatabaseEnginePool）
3. 不实现消息队列的高级特性（延迟队列、死信队列等）

## 决策

### 决策 1：客户端缓存策略

**选择：双层缓存 + 实例 Key**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    客户端缓存结构                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  _default_client: Redis              # 默认客户端（共享）           │
│                                                                     │
│  _db_clients: dict[int, Redis]       # 同实例不同 DB                │
│      key = db_index                                                 │
│      用于：同一 Redis 实例的逻辑隔离                                 │
│                                                                     │
│  _instance_clients: dict[str, Redis] # 不同实例（新增）             │
│      key = f"{host}:{port}"                                         │
│      用于：物理隔离场景                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**理由：**
- 分层缓存避免连接爆炸
- 实例 Key 简单可靠，便于查找和清理
- 与现有 `_db_clients` 结构一致

**替代方案：**
- 单层缓存统一管理：实现复杂，需要重构现有逻辑
- 不缓存直接创建：性能差，每次请求都创建连接

### 决策 2：判断物理隔离 vs 逻辑隔离

**规则：**

```python
def _is_physical_isolation(config: TenantCacheConfig) -> bool:
    """判断是否使用物理隔离"""
    # 有独立 host 且非空，使用物理隔离
    return bool(config and config.host)
```

**理由：**
- `host` 为空表示使用默认实例
- 简单明确的判断条件
- 与配置字段的语义一致

### 决策 3：存储管理器的独立客户端

**选择：延迟创建 + 缓存**

```python
class TenantStorageManager:
    _default_storage: MinioStorage
    _instance_storages: dict[str, MinioStorage]  # key = endpoint

    async def get_storage(self, config: TenantStorageConfig) -> MinioStorage:
        if not config or not config.endpoint:
            return self._default_storage

        key = config.endpoint
        if key in self._instance_storages:
            return self._instance_storages[key]

        storage = await self._create_storage(config)
        self._instance_storages[key] = storage
        return storage
```

**理由：**
- 不同 endpoint 对应不同的存储服务
- access_key/secret_key 随 endpoint 变化
- 缓存避免重复创建

### 决策 4：队列和发布订阅管理器

**选择：统一使用 TenantCacheManager 的客户端**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    队列/发布订阅架构                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TenantQueueManager                                                 │
│  ├── 依赖 TenantCacheManager 获取 Redis 客户端                      │
│  ├── 支持 Redis Stream 作为队列实现                                  │
│  └── 未来可扩展 RabbitMQ/Kafka 适配器                               │
│                                                                     │
│  TenantPubSubManager                                                │
│  ├── 依赖 TenantCacheManager 获取 Redis 客户端                      │
│  ├── 支持 Redis PubSub 作为实现                                     │
│  └── 未来可扩展 Kafka 适配器                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**理由：**
- 复用现有 Redis 客户端管理逻辑
- 简化实现，避免重复代码
- 当前项目使用 Redis 作为队列和发布订阅后端

**替代方案：**
- 独立管理客户端：重复实现连接池管理
- 仅支持 Redis：限制扩展性

## 风险 / 权衡

### 风险 1：连接数爆炸

**风险：** 每个物理隔离租户都会创建独立的 Redis/MinIO 连接

**缓解：**
- 实现客户端 LRU 淘汰机制
- 设置最大实例数限制（默认 50）
- 定期清理空闲连接

### 风险 2：密码泄露

**风险：** 解密后的密码存在于内存中

**缓解：**
- 密码仅在创建客户端时解密
- 不在日志中输出敏感信息
- 客户端缓存不包含明文密码

### 风险 3：配置不一致

**风险：** 资源配置表中的配置与协议定义不一致

**缓解：**
- `_load_xxx_config()` 方法验证字段完整性
- 单元测试覆盖配置加载逻辑
- 文档明确字段对应关系

### 权衡 1：简化 vs 灵活性

**选择：** 当前仅支持 Redis 作为队列/发布订阅后端

**权衡：** 牺牲了 RabbitMQ/Kafka 的灵活性，换取实现简单

**理由：** 项目当前使用 Redis，未来可按需扩展

## 实现计划

### 阶段 1：验证已有修改

1. 检查 Tenant 模型字段完整性
2. 验证迁移脚本正确性
3. 测试缓存 L2 序列化/反序列化

### 阶段 2：TenantCacheManager 增强

1. 添加 `_instance_clients` 缓存
2. 修改 `get_client()` 支持物理隔离
3. 实现实例级客户端创建和清理

### 阶段 3：TenantStorageManager 增强

1. 添加 `_instance_storages` 缓存
2. 修改各方法支持独立存储服务
3. 实现存储客户端创建和清理

### 阶段 4：新增管理器

1. 创建 TenantQueueManager
2. 创建 TenantPubSubManager
3. 注册到全局工厂

### 阶段 5：测试与文档

1. 单元测试覆盖
2. 集成测试验证
3. 更新 API 文档

## 开放问题

1. **MinIO 客户端是否支持异步？** 当前使用同步客户端，是否需要迁移到异步？
2. **物理隔离的性能基准？** 需要压测确定合理的连接池大小和淘汰策略
