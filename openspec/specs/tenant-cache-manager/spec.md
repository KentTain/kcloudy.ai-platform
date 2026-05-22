## ADDED Requirements

### Requirement: Redis DB 路由管理

系统 SHALL 根据租户配置路由到独立 Redis DB。

#### Scenario: 租户配置独立 Redis DB
- **WHEN** 租户配置了 cache_db（如 3）
- **THEN** 该租户的所有缓存操作使用 Redis DB 3

#### Scenario: 租户无独立 Redis DB 配置
- **WHEN** 租户未配置 cache_db
- **THEN** 使用默认 Redis DB（DB 0）
- **AND** 使用 {tenant_id}:key 前缀进行逻辑隔离

### Requirement: 缓存操作隔离

系统 SHALL 自动将缓存操作路由到正确的 Redis DB。

#### Scenario: 设置缓存到独立 Redis DB
- **WHEN** 租户配置了 cache_db=3 且调用缓存设置接口
- **THEN** 数据存储到 Redis DB 3
- **AND** 无需手动切换 DB

#### Scenario: 设置缓存到默认 Redis DB
- **WHEN** 租户未配置 cache_db 且调用缓存设置接口
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
