## ADDED Requirements

### Requirement: Redis 连接管理
系统 SHALL 提供统一的 Redis 连接管理，支持单机、集群、哨兵模式。

#### Scenario: 单机模式连接
- **WHEN** 配置 `redis.mode=single`
- **THEN** 系统创建单机 Redis 连接池

#### Scenario: 集群模式连接
- **WHEN** 配置 `redis.mode=cluster`
- **THEN** 系统创建集群 Redis 连接

### Requirement: RedisUtil 工具类
系统 SHALL 提供 `RedisUtil` 工具类，封装常用 Redis 操作。

#### Scenario: 字符串操作
- **WHEN** 调用 `RedisUtil.set("key", "value", ttl=60)`
- **THEN** Redis 存储键值对，60 秒后过期

#### Scenario: 获取不存在的键
- **WHEN** 调用 `RedisUtil.get("nonexistent")`
- **THEN** 返回 `None`

#### Scenario: 删除键
- **WHEN** 调用 `RedisUtil.delete("key")`
- **THEN** 键被删除，返回删除数量

### Requirement: 连接池管理
系统 SHALL 使用连接池管理 Redis 连接，支持配置最大连接数、超时等参数。

#### Scenario: 连接池配置
- **WHEN** 配置 `redis.single.connection-pool.max-connections=50`
- **THEN** 连接池最大连接数为 50

#### Scenario: 连接复用
- **WHEN** 多次调用 RedisUtil 方法
- **THEN** 复用连接池中的连接

### Requirement: 健康检查
系统 SHALL 提供 Redis 连接健康检查功能。

#### Scenario: 健康检查成功
- **WHEN** 调用 `RedisUtil.health_check()`
- **THEN** 返回 `True`（连接正常）

#### Scenario: 健康检查失败
- **WHEN** Redis 服务不可用时调用 `RedisUtil.health_check()`
- **THEN** 返回 `False`
