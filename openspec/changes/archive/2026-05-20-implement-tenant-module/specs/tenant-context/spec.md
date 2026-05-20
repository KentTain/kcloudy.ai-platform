## ADDED Requirements

### Requirement: 租户上下文存储

系统 SHALL 使用 ContextVar 实现线程安全的租户上下文存储。

#### Scenario: 设置租户上下文
- **WHEN** 调用 `TenantContext.set_current_tenant(tenant)` 设置租户信息
- **THEN** 当前请求线程可以通过 `TenantContext.get_current_tenant()` 获取到该租户

#### Scenario: 获取不存在的租户上下文
- **WHEN** 在未设置租户上下文时调用 `TenantContext.get_current_tenant()`
- **THEN** 返回 None

#### Scenario: 线程隔离
- **WHEN** 在不同线程中设置不同的租户上下文
- **THEN** 每个线程获取到的租户上下文互不影响

### Requirement: 租户 ID 获取

系统 SHALL 提供便捷方法获取当前租户 ID。

#### Scenario: 获取租户 ID
- **WHEN** 已设置租户上下文时调用 `get_tenant_id()`
- **THEN** 返回当前租户的 ID

#### Scenario: 未设置租户上下文时获取租户 ID
- **WHEN** 未设置租户上下文时调用 `get_tenant_id()`
- **THEN** 返回 None

### Requirement: 上下文清理

系统 SHALL 在请求结束后自动清理租户上下文。

#### Scenario: 清理租户上下文
- **WHEN** 调用 `TenantContext.clear()` 清理上下文
- **THEN** 再次调用 `get_current_tenant()` 返回 None

#### Scenario: 请求结束自动清理
- **WHEN** 请求处理完成（无论成功或异常）
- **THEN** 租户上下文被自动清理

### Requirement: 租户信息封装

系统 SHALL 封装租户基本信息，至少包含以下字段：
- tenant_id: 租户 ID
- tenant_code: 租户编码
- tenant_name: 租户名称
- status: 租户状态

#### Scenario: 获取租户基本信息
- **WHEN** 调用 `get_current_tenant()` 获取租户信息
- **THEN** 返回包含 tenant_id、tenant_code、tenant_name、status 的租户对象
