## ADDED Requirements

### Requirement: StorageProvider 接口定义
系统 SHALL 使用 Python Protocol 定义 `StorageProvider` 接口，包含 upload、download、delete、get_presigned_url 方法。

#### Scenario: Protocol 类型检查
- **WHEN** 定义一个实现 StorageProvider 所有方法的类
- **THEN** 该类被视为 StorageProvider 类型

#### Scenario: 缺少方法实现
- **WHEN** 定义一个缺少 upload 方法的类
- **THEN** 类型检查器报告该类不满足 StorageProvider 协议

### Requirement: QueueProvider 接口定义
系统 SHALL 使用 Python Protocol 定义 `QueueProvider` 接口，包含 enqueue、dequeue、ack 方法。

#### Scenario: 消息入队
- **WHEN** 调用 `provider.enqueue("queue_name", {"data": "value"})`
- **THEN** 返回消息 ID

#### Scenario: 消息出队
- **WHEN** 调用 `provider.dequeue("queue_name", count=5)`
- **THEN** 返回最多 5 条消息列表

### Requirement: PubSubProvider 接口定义
系统 SHALL 使用 Python Protocol 定义 `PubSubProvider` 接口，包含 publish、subscribe、unsubscribe 方法。

#### Scenario: 发布消息
- **WHEN** 调用 `provider.publish("topic", {"data": "value"})`
- **THEN** 消息发布到指定主题

#### Scenario: 订阅主题
- **WHEN** 调用 `provider.subscribe("topic", handler_func)`
- **THEN** 该主题的消息被 handler_func 处理

### Requirement: LockProvider 接口定义
系统 SHALL 使用 Python Protocol 定义 `LockProvider` 接口，包含 acquire、release、extend 方法。

#### Scenario: 获取锁
- **WHEN** 调用 `provider.acquire("lock_key", ttl=30)`
- **THEN** 返回 Lock 对象或 None（获取失败）

#### Scenario: 释放锁
- **WHEN** 调用 `provider.release(lock)`
- **THEN** 锁被释放

#### Scenario: 延长锁
- **WHEN** 调用 `provider.extend(lock, ttl=60)`
- **THEN** 锁的 TTL 延长到 60 秒
