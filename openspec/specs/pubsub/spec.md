## ADDED Requirements

### Requirement: Redis PubSub 实现
系统 SHALL 基于 Redis PubSub 实现发布订阅功能。

#### Scenario: 发布消息
- **WHEN** 调用 `pubsub.publish("notifications", {"type": "alert", "message": "系统告警"})`
- **THEN** 消息发布到 "notifications" 频道

#### Scenario: 订阅频道
- **WHEN** 调用 `pubsub.subscribe("notifications", handler_func)`
- **THEN** handler_func 接收到该频道的所有消息

#### Scenario: 取消订阅
- **WHEN** 调用 `pubsub.unsubscribe("notifications")`
- **THEN** 停止接收该频道的消息

### Requirement: 发布订阅工厂
系统 SHALL 提供发布订阅工厂，根据配置 `messaging.pubsub.use` 返回对应实现。

#### Scenario: 获取 Redis PubSub
- **WHEN** 配置 `messaging.pubsub.use=redis`
- **THEN** 工厂返回 RedisPubSub 实例

### Requirement: 消息处理器接口
系统 SHALL 定义消息处理器接口，支持单主题和多主题处理。

#### Scenario: 单主题处理器
- **WHEN** 继承 `SingleTopicMessageHandler` 并设置 `topic="notifications"`
- **THEN** 自动订阅 "notifications" 主题

#### Scenario: 多主题处理器
- **WHEN** 继承 `MultiTopicMessageHandler` 并设置 `topics=["orders", "payments"]`
- **THEN** 自动订阅多个主题

### Requirement: 异步消息处理
系统 SHALL 支持异步消息处理，处理器为 async 函数。

#### Scenario: 异步处理器
- **WHEN** 定义 `async def handle(topic, message)` 处理器
- **THEN** 消息被异步处理，不阻塞主线程
