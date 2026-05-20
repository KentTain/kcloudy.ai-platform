## ADDED Requirements

### Requirement: Redis Stream 队列实现
系统 SHALL 基于 Redis Stream 实现消息队列，支持消息入队、出队、确认功能。

#### Scenario: 消息入队
- **WHEN** 调用 `queue.enqueue("orders", {"order_id": "123", "action": "create"})`
- **THEN** 消息写入 Redis Stream，返回消息 ID

#### Scenario: 批量出队
- **WHEN** 调用 `queue.dequeue("orders", count=10)`
- **THEN** 返回最多 10 条未确认的消息

#### Scenario: 消息确认
- **WHEN** 调用 `queue.ack("orders", message_id)`
- **THEN** 消息标记为已处理

### Requirement: 消费者组支持
系统 SHALL 支持 Redis Stream 消费者组模式。

#### Scenario: 创建消费者组
- **WHEN** 调用 `queue.create_consumer_group("orders", "workers")`
- **THEN** 创建名为 "workers" 的消费者组

#### Scenario: 消费者组读取
- **WHEN** 消费者组中的消费者读取消息
- **THEN** 消息被分配给一个消费者，避免重复消费

### Requirement: 队列工厂
系统 SHALL 提供队列工厂，根据配置 `messaging.queue.use` 返回对应的队列实现。

#### Scenario: 获取 Redis 队列
- **WHEN** 配置 `messaging.queue.use=redis`
- **THEN** 工厂返回 RedisQueue 实例

### Requirement: 消息处理器注册
系统 SHALL 支持注册消息处理器，自动消费队列消息。

#### Scenario: 注册处理器
- **WHEN** 注册 `QueueHandler` 并指定队列名
- **THEN** 处理器自动消费该队列的消息

#### Scenario: 处理器并发配置
- **WHEN** 配置 `handler.concurrency=5`
- **THEN** 启动 5 个并发消费者处理消息
