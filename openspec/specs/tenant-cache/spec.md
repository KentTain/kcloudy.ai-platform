## ADDED Requirements

### Requirement: 两级缓存架构

系统 SHALL 采用 L1 本地内存 + L2 Redis 两级缓存策略。

#### Scenario: L1 缓存命中
- **WHEN** 租户信息在 L1 本地缓存中存在
- **THEN** 直接返回 L1 缓存数据，不访问 Redis

#### Scenario: L1 未命中 L2 命中
- **WHEN** 租户信息在 L1 本地缓存中不存在
- **AND** 在 L2 Redis 缓存中存在
- **THEN** 从 Redis 获取数据，回填 L1 缓存，然后返回

#### Scenario: 两级缓存均未命中
- **WHEN** 租户信息在 L1 和 L2 缓存中均不存在
- **THEN** 从数据库查询，写入 L1 和 L2 缓存，然后返回

### Requirement: 本地缓存限制

系统 SHALL 限制 L1 本地缓存的最大条目数。

#### Scenario: 本地缓存最大条目限制
- **WHEN** 本地缓存条目数达到 1000
- **THEN** 使用 LRU 策略淘汰最久未使用的条目

### Requirement: Redis 缓存 TTL

系统 SHALL 为 L2 Redis 缓存设置 TTL。

#### Scenario: Redis 缓存过期
- **WHEN** Redis 缓存存储时间超过 5 分钟
- **THEN** 缓存自动过期

### Requirement: 缓存更新同步

系统 SHALL 在租户信息更新时同步更新缓存。

#### Scenario: 更新租户信息时更新缓存
- **WHEN** 租户信息被更新
- **THEN** 更新 L1 本地缓存
- **AND** 更新 L2 Redis 缓存
- **AND** 发布缓存失效消息

### Requirement: 缓存失效通知

系统 SHALL 通过 Redis Pub/Sub 同步缓存失效。

#### Scenario: 缓存失效通知
- **WHEN** 收到缓存失效消息 `{"tenant_id": "tenant_001"}`
- **THEN** 清除本地 L1 缓存中 `tenant_001` 的租户信息

### Requirement: 缓存主动清除

系统 SHALL 提供主动清除缓存的方法。

#### Scenario: 主动清除缓存
- **WHEN** 调用 `TenantCache.invalidate("tenant_001")`
- **THEN** 清除 L1 本地缓存
- **AND** 清除 L2 Redis 缓存
- **AND** 发布缓存失效消息通知其他实例
