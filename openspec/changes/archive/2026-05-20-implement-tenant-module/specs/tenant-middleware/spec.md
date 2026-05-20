## ADDED Requirements

### Requirement: 租户标识解析

系统 SHALL 支持多种方式解析租户标识，优先级从高到低：
1. 请求头 `X-Tenant-Id`
2. Token 中的 `tenant_id`
3. 用户默认租户

#### Scenario: 从请求头解析租户标识
- **WHEN** 请求包含 `X-Tenant-Id: tenant_001` 头
- **THEN** 系统使用 `tenant_001` 作为当前租户 ID

#### Scenario: 从 Token 解析租户标识
- **WHEN** Token payload 包含 `tenant_id: tenant_002` 且请求头无 `X-Tenant-Id`
- **THEN** 系统使用 `tenant_002` 作为当前租户 ID

#### Scenario: 使用用户默认租户
- **WHEN** 请求头和 Token 均无租户标识
- **THEN** 系统使用用户关联的默认租户 ID

#### Scenario: 无法解析租户标识
- **WHEN** 请求头、Token 和用户默认租户均无法获取租户标识
- **THEN** 返回 HTTP 400 错误

### Requirement: 租户状态验证

系统 SHALL 验证租户状态，仅允许有效租户访问。

#### Scenario: 租户不存在
- **WHEN** 解析到的租户 ID 对应的租户不存在
- **THEN** 返回 HTTP 404 错误，消息为 "租户不存在"

#### Scenario: 租户已停用
- **WHEN** 租户状态为 `inactive`
- **THEN** 返回 HTTP 403 错误，消息为 "租户已停用"

#### Scenario: 租户已过期
- **WHEN** 租户的 `expired_at` 早于当前时间
- **THEN** 返回 HTTP 403 错误，消息为 "租户已过期"

#### Scenario: 租户有效
- **WHEN** 租户存在、状态为 `active` 且未过期
- **THEN** 请求继续处理

### Requirement: 租户上下文注入

系统 SHALL 在请求处理前将租户信息注入上下文。

#### Scenario: 注入租户上下文
- **WHEN** 租户验证通过
- **THEN** 租户信息被存入 `TenantContext`
- **AND** 业务代码可通过 `get_current_tenant()` 获取租户信息

### Requirement: 请求结束清理

系统 SHALL 在请求处理完成后自动清理租户上下文。

#### Scenario: 请求成功后清理
- **WHEN** 请求处理成功
- **THEN** 租户上下文被清理

#### Scenario: 请求异常后清理
- **WHEN** 请求处理过程中发生异常
- **THEN** 租户上下文仍被清理

### Requirement: 用户访问权限验证

系统 SHALL 验证用户是否有权访问指定租户。

#### Scenario: 用户无权访问租户
- **WHEN** 用户不属于请求的租户
- **THEN** 返回 HTTP 403 错误，消息为 "无权访问该租户"

#### Scenario: 用户有权访问租户
- **WHEN** 用户属于请求的租户
- **THEN** 请求继续处理
