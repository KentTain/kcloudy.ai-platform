## ADDED Requirements

### Requirement: 发布订阅资源管理

系统 SHALL 提供租户级发布订阅资源管理能力。

#### Scenario: 获取发布订阅管理器实例
- **WHEN** 调用 get_pubsub_manager()
- **THEN** 返回全局 TenantPubSubManager 单例

#### Scenario: 发布订阅管理器初始化
- **WHEN** 应用启动时调用 init_pubsub_manager()
- **THEN** 使用默认 Redis 客户端初始化发布订阅管理器

### Requirement: 发布订阅物理隔离

系统 SHALL 支持连接不同的消息实例。

#### Scenario: 连接独立消息实例
- **WHEN** 租户配置了 TenantPubSubConfig 的 host="pubsub-tenant.example.com"
- **THEN** 使用该实例进行发布订阅操作

#### Scenario: 使用默认消息实例
- **WHEN** 租户未配置消息实例
- **THEN** 使用默认 Redis 实例的 PubSub 功能

### Requirement: 发布订阅类型支持

系统 SHALL 支持多种发布订阅类型。

#### Scenario: Redis PubSub
- **WHEN** 配置 type="redis"
- **THEN** 使用 Redis PubSub 作为实现

#### Scenario: Kafka 发布订阅
- **WHEN** 配置 type="kafka"
- **THEN** 使用 Kafka 作为发布订阅实现

### Requirement: 频道隔离

系统 SHALL 根据租户配置隔离发布订阅频道。

#### Scenario: 物理隔离频道
- **WHEN** 配置了独立消息实例
- **THEN** 消息发布到独立实例的频道
- **AND** 频道名不添加前缀

#### Scenario: 逻辑隔离频道
- **WHEN** 使用默认 Redis 实例
- **THEN** 频道名添加 {tenant_id}:channel: 前缀

### Requirement: 发布订阅操作

系统 SHALL 提供完整的发布订阅操作接口。

#### Scenario: 发布消息
- **WHEN** 调用 publish() 发布消息到频道
- **THEN** 消息发布到正确的频道
- **AND** 返回订阅者数量

#### Scenario: 订阅频道
- **WHEN** 调用 subscribe() 订阅频道
- **THEN** 开始接收该频道的消息

#### Scenario: 取消订阅
- **WHEN** 调用 unsubscribe() 取消订阅
- **THEN** 停止接收该频道的消息

### Requirement: 发布订阅客户端缓存

系统 SHALL 缓存发布订阅客户端连接。

#### Scenario: 复用发布订阅客户端
- **WHEN** 访问已创建的消息实例
- **THEN** 返回缓存的客户端

#### Scenario: 创建发布订阅客户端
- **WHEN** 访问新的消息实例
- **THEN** 创建新客户端并缓存

### Requirement: 消息回调

系统 SHALL 支持消息回调处理。

#### Scenario: 注册消息回调
- **WHEN** 订阅频道时注册回调函数
- **THEN** 收到消息时调用该回调

#### Scenario: 异常处理
- **WHEN** 回调函数抛出异常
- **THEN** 记录错误日志
- **AND** 继续处理后续消息
