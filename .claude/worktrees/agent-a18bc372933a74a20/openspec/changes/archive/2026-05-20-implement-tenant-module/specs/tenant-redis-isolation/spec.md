## ADDED Requirements

### Requirement: 缓存 Key 隔离

系统 SHALL 自动为 Redis 缓存 Key 添加租户前缀。

#### Scenario: 设置缓存自动添加前缀
- **WHEN** 调用 `RedisUtil.set("user:123", data)` 且当前租户为 `tenant_001`
- **THEN** 实际存储 Key 为 `tenant_001:user:123`

#### Scenario: 获取缓存自动添加前缀
- **WHEN** 调用 `RedisUtil.get("user:123")` 且当前租户为 `tenant_001`
- **THEN** 实际查询 Key 为 `tenant_001:user:123`

#### Scenario: 删除缓存自动添加前缀
- **WHEN** 调用 `RedisUtil.delete("user:123")` 且当前租户为 `tenant_001`
- **THEN** 实际删除 Key 为 `tenant_001:user:123`

#### Scenario: 管理员场景跳过前缀
- **WHEN** 调用 `RedisUtil.set("system:config", data, skip_tenant=True)`
- **THEN** 实际存储 Key 为 `system:config`（无租户前缀）

### Requirement: 队列隔离

系统 SHALL 自动为 Redis Stream 队列 Key 添加租户前缀。

#### Scenario: 入队自动添加前缀
- **WHEN** 调用 `RedisUtil.xadd("queue:email:send", message)` 且当前租户为 `tenant_001`
- **THEN** 实际写入 Stream Key 为 `tenant_001:queue:email:send`

#### Scenario: 读取队列自动添加前缀
- **WHEN** 调用 `RedisUtil.xread("queue:email:send")` 且当前租户为 `tenant_001`
- **THEN** 实际读取 Stream Key 为 `tenant_001:queue:email:send`

### Requirement: 发布订阅隔离

系统 SHALL 自动为 Redis Channel 添加租户前缀。

#### Scenario: 发布消息自动添加前缀
- **WHEN** 调用 `RedisUtil.publish("notifications", message)` 且当前租户为 `tenant_001`
- **THEN** 实际发布到 Channel `tenant_001:channel:notifications`

#### Scenario: 订阅频道自动添加前缀
- **WHEN** 调用 `RedisUtil.subscribe("notifications")` 且当前租户为 `tenant_001`
- **THEN** 实际订阅 Channel `tenant_001:channel:notifications`

### Requirement: 分布式锁隔离

系统 SHALL 自动为 Redis Lock Key 添加租户前缀。

#### Scenario: 获取锁自动添加前缀
- **WHEN** 调用 `RedisUtil.acquire_lock("order:12345")` 且当前租户为 `tenant_001`
- **THEN** 实际 Lock Key 为 `tenant_001:lock:order:12345`

#### Scenario: 释放锁自动添加前缀
- **WHEN** 调用 `RedisUtil.release_lock("order:12345")` 且当前租户为 `tenant_001`
- **THEN** 实际释放 Lock Key 为 `tenant_001:lock:order:12345`

### Requirement: 跨租户隔离验证

系统 SHALL 确保不同租户的 Redis 数据相互隔离。

#### Scenario: 租户 A 无法访问租户 B 的缓存
- **WHEN** 租户 A 尝试获取 Key `user:123`
- **THEN** 无法获取到租户 B 设置的 `tenant_002:user:123` 数据

#### Scenario: 租户 A 无法消费租户 B 的队列
- **WHEN** 租户 A 消费队列 `queue:email:send`
- **THEN** 只能消费 `tenant_001:queue:email:send` 中的消息
