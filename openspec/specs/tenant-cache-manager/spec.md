# tenant-cache-manager Specification

## Purpose
租户缓存管理器规范，提供 Redis DB 路由、缓存操作隔离和 Redis 实例物理隔离能力。
## Requirements
### Requirement: Redis DB 路由管理

系统 SHALL 根据租户配置路由到独立 Redis DB 或独立 Redis 实例。

#### Scenario: 租户配置独立 Redis DB
- **WHEN** 租户配置了 cache_db（如 3）且未配置 host
- **THEN** 该租户的所有缓存操作使用默认实例的 Redis DB 3

#### Scenario: 租户配置独立 Redis 实例
- **WHEN** 租户配置了 host="redis-tenant.example.com"
- **THEN** 该租户的所有缓存操作使用独立 Redis 实例

#### Scenario: 租户无独立 Redis 配置
- **WHEN** 租户未配置 cache_db 且未配置 host
- **THEN** 使用默认 Redis DB（DB 0）
- **AND** 使用 {tenant_id}:key 前缀进行逻辑隔离

### Requirement: 缓存操作隔离

系统 SHALL 自动将缓存操作路由到正确的 Redis 实例或 DB。

#### Scenario: 设置缓存到独立实例
- **WHEN** 租户配置了 host 且调用缓存设置接口
- **THEN** 数据存储到独立 Redis 实例
- **AND** Key 不添加租户前缀（物理隔离）

#### Scenario: 设置缓存到独立 DB
- **WHEN** 租户仅配置了 db=3 且调用缓存设置接口
- **THEN** 数据存储到默认实例的 Redis DB 3
- **AND** Key 不添加租户前缀

#### Scenario: 设置缓存到默认 Redis
- **WHEN** 租户未配置任何隔离参数且调用缓存设置接口
- **THEN** 数据存储到 Redis DB 0
- **AND** Key 自动添加 {tenant_id}: 前缀

### Requirement: 缓存读取隔离

系统 SHALL 自动从正确的 Redis DB 读取缓存。

#### Scenario: 从独立 Redis DB 读取缓存
- **WHEN** 租户配置了 cache_db=3 且调用缓存读取接口
- **THEN** 从 Redis DB 3 读取数据

#### Scenario: 从默认 Redis DB 读取缓存
- **WHEN** 租户未配置 cache_db 且调用缓存读取接口
- **THEN** 从 Redis DB 0 读取数据
- **AND** Key 自动添加 {tenant_id}: 前缀

### Requirement: Redis 客户端缓存

系统 SHALL 缓存 Redis 客户端连接以提高性能。

#### Scenario: 复用已创建的 Redis 客户端
- **WHEN** 请求访问某个 Redis DB 且客户端已存在
- **THEN** 直接返回缓存的客户端

#### Scenario: 创建新的 Redis 客户端
- **WHEN** 请求访问某个 Redis DB 且客户端不存在
- **THEN** 创建新的 Redis 客户端并缓存

### Requirement: DB 编号范围验证

系统 SHALL 验证 cache_db 配置的有效性。

#### Scenario: 验证 DB 编号范围
- **WHEN** 配置 cache_db 时
- **THEN** 验证值在 0-15 范围内
- **AND** 超出范围时返回错误

#### Scenario: DB 编号冲突检测
- **WHEN** 配置 cache_db 时
- **THEN** 检查该 DB 是否已被其他租户使用
- **AND** 冲突时提示选择其他 DB 编号

### Requirement: Redis 实例级物理隔离

系统 SHALL 支持根据 TenantCacheConfig 连接不同的 Redis 实例。

#### Scenario: 连接独立 Redis 实例
- **WHEN** 租户配置了 host="redis-tenant-a.example.com" 和 port=6380
- **THEN** 系统创建到该实例的独立 Redis 客户端
- **AND** 所有缓存操作通过该客户端执行

#### Scenario: 使用默认 Redis 实例
- **WHEN** 租户未配置 host 或 host 为空
- **THEN** 使用默认 Redis 客户端
- **AND** 根据 db 配置决定逻辑隔离或 DB 隔离

### Requirement: Redis 实例客户端缓存

系统 SHALL 缓存不同 Redis 实例的客户端连接。

#### Scenario: 复用已缓存的实例客户端
- **WHEN** 请求连接 host="redis-a.com:6379" 且该实例客户端已存在
- **THEN** 返回缓存的客户端

#### Scenario: 创建新的实例客户端
- **WHEN** 请求连接 host="redis-b.com:6380" 且该实例客户端不存在
- **THEN** 使用配置的 host/port/password 创建新客户端
- **AND** 将客户端缓存到 _instance_clients

#### Scenario: 客户端认证
- **WHEN** 配置了 password
- **THEN** 创建客户端时使用该密码进行认证

### Requirement: 客户端连接池管理

系统 SHALL 管理实例客户端的生命周期。

#### Scenario: LRU 淘汰空闲客户端
- **WHEN** 实例客户端数量超过最大限制（默认 50）
- **THEN** 淘汰最近最少使用的客户端
- **AND** 关闭淘汰客户端的连接

#### Scenario: 定期清理空闲客户端
- **WHEN** 客户端空闲时间超过阈值（默认 300 秒）
- **THEN** 关闭该客户端并从缓存移除

### Requirement: 密码安全处理

系统 SHALL 安全处理 Redis 密码。

#### Scenario: 密码解密
- **WHEN** 配置中的密码为加密存储
- **THEN** 在创建客户端前解密密码
- **AND** 解密后的密码不记录到日志

#### Scenario: 密码为空
- **WHEN** 配置中 password 为空字符串
- **THEN** 创建无需认证的客户端连接

