# tenant-queue-manager Specification

## Purpose
租户级队列管理器规范，提供消息队列、消费者组管理和物理隔离能力。

## ADDED Requirements

### Requirement: 队列资源管理

系统 SHALL 提供租户级队列资源管理能力。

#### Scenario: 获取队列管理器实例
- **WHEN** 调用 get_queue_manager()
- **THEN** 返回全局 TenantQueueManager 单例

#### Scenario: 队列管理器初始化
- **WHEN** 应用启动时调用 init_queue_manager()
- **THEN** 使用默认 Redis 客户端初始化队列管理器

### Requirement: 队列物理隔离

系统 SHALL 支持连接不同的队列实例。

#### Scenario: 连接独立队列实例
- **WHEN** 租户配置了 TenantQueueConfig 的 host="queue-tenant.example.com"
- **THEN** 使用该实例进行队列操作

#### Scenario: 使用默认队列实例
- **WHEN** 租户未配置队列实例
- **THEN** 使用默认 Redis 实例的 Stream 功能

### Requirement: 队列类型支持

系统 SHALL 支持多种队列类型。

#### Scenario: Redis Stream 队列
- **WHEN** 配置 type="redis"
- **THEN** 使用 Redis Stream 作为队列实现

#### Scenario: RabbitMQ 队列
- **WHEN** 配置 type="rabbitmq"
- **THEN** 使用 RabbitMQ 作为队列实现
- **AND** 使用配置的 vhost

#### Scenario: Kafka 队列
- **WHEN** 配置 type="kafka"
- **THEN** 使用 Kafka 作为队列实现

### Requirement: 消息队列隔离

系统 SHALL 根据租户配置隔离消息队列。

#### Scenario: 物理隔离队列
- **WHEN** 配置了独立队列实例
- **THEN** 消息存储在独立实例
- **AND** 队列名不添加前缀

#### Scenario: 逻辑隔离队列
- **WHEN** 使用默认 Redis 实例
- **THEN** 队列名添加 {tenant_id}:queue: 前缀

### Requirement: 队列操作

系统 SHALL 提供完整的队列操作接口。

#### Scenario: 发送消息
- **WHEN** 调用 xadd() 发送消息
- **THEN** 消息写入正确的队列
- **AND** 返回消息 ID

#### Scenario: 消费消息
- **WHEN** 调用 xreadgroup() 消费消息
- **THEN** 从正确的队列读取消息
- **AND** 支持消费者组模式

#### Scenario: 确认消息
- **WHEN** 调用 xack() 确认消息
- **THEN** 消息标记为已处理

### Requirement: 队列客户端缓存

系统 SHALL 缓存队列客户端连接。

#### Scenario: 复用队列客户端
- **WHEN** 访问已创建的队列实例
- **THEN** 返回缓存的客户端

#### Scenario: 创建队列客户端
- **WHEN** 访问新的队列实例
- **THEN** 创建新客户端并缓存
