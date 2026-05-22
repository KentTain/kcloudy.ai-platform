## ADDED Requirements

### Requirement: 独立 Redis DB 物理隔离

系统 SHALL 支持租户使用独立的 Redis DB，实现缓存数据物理隔离。

#### Scenario: 租户使用独立 Redis DB
- **WHEN** 租户配置了独立 Redis DB（cache_db 不为空）
- **THEN** 租户缓存数据存储在独立 Redis DB 中
- **AND** 缓存数据完全物理隔离，无法被其他租户访问

#### Scenario: 独立 Redis DB 无需 Key 前缀
- **WHEN** 租户使用独立 Redis DB
- **THEN** 缓存 Key 无需添加 {tenant_id}: 前缀
- **AND** Key 直接使用原始 Key

### Requirement: 缓存模式选择

系统 SHALL 支持逻辑隔离和物理隔离两种缓存模式。

#### Scenario: 逻辑隔离模式
- **WHEN** 租户未配置独立 Redis DB
- **THEN** 使用共享 Redis DB + {tenant_id}: Key 前缀
- **AND** Key 自动添加租户前缀

#### Scenario: 物理隔离模式
- **WHEN** 租户配置了独立 Redis DB
- **THEN** 使用独立 Redis DB
- **AND** Key 不添加租户前缀

### Requirement: 队列和发布订阅隔离模式

系统 SHALL 根据缓存隔离模式自动选择队列和发布订阅的隔离方式。

#### Scenario: 物理隔离租户的队列
- **WHEN** 租户使用独立 Redis DB 且操作队列
- **THEN** 队列数据存储在独立 Redis DB 中
- **AND** 无需队列名称前缀

#### Scenario: 物理隔离租户的发布订阅
- **WHEN** 租户使用独立 Redis DB 且操作发布订阅
- **THEN** 频道数据在独立 Redis DB 中
- **AND** 无需频道名称前缀
