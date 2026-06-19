# tenant-context-injection Specification

## Purpose
TBD - created by archiving change complete-iam-multi-tenancy. Update Purpose after archive.
## Requirements
### Requirement: TenantMiddleware 解析 X-Tenant-Id 请求头

系统 SHALL 从 HTTP 请求头 `X-Tenant-Id` 中解析租户标识，并将其注入到请求上下文中，供后续业务逻辑使用。

#### Scenario: 正常请求带 X-Tenant-Id
- **GIVEN** 请求头包含有效的 `X-Tenant-Id: tenant-123`
- **WHEN** 请求进入 TenantMiddleware
- **THEN** 中间件从请求头解析出租户 ID `tenant-123`
- **AND** 通过 TenantProvider 获取租户信息
- **AND** 验证租户状态为 ACTIVE 且未过期
- **AND** 将租户信息注入 TenantContext

#### Scenario: 请求不带 X-Tenant-Id
- **GIVEN** 请求头不包含 `X-Tenant-Id`
- **WHEN** 请求进入 TenantMiddleware
- **THEN** 中间件返回 HTTP 400 错误，消息为 "无法解析租户标识，请在请求头中提供 X-Tenant-Id"

#### Scenario: 请求带无效租户 ID
- **GIVEN** 请求头包含 `X-Tenant-Id: nonexistent`
- **WHEN** 请求进入 TenantMiddleware 且租户不存在
- **THEN** 中间件返回 HTTP 404 错误，消息为 "租户不存在"

#### Scenario: 请求带已停用租户 ID
- **GIVEN** 请求头包含 `X-Tenant-Id: inactive-tenant`
- **AND** 该租户状态为 INACTIVE
- **WHEN** 请求进入 TenantMiddleware
- **THEN** 中间件返回 HTTP 403 错误，消息为 "租户已停用"

#### Scenario: 请求带已过期租户 ID
- **GIVEN** 请求头包含 `X-Tenant-Id: expired-tenant`
- **AND** 该租户已过期
- **WHEN** 请求进入 TenantMiddleware
- **THEN** 中间件返回 HTTP 403 错误，消息为 "租户已过期"

#### Scenario: 跳过的路径不需要租户
- **GIVEN** 请求路径为 `/health` 或 `/docs`
- **WHEN** 请求进入 TenantMiddleware
- **THEN** 中间件跳过租户验证，直接放行

---

### Requirement: TenantContext 提供租户信息访问

系统 SHALL 通过 TenantContext 提供获取当前租户信息的能力，供业务模块查询和使用。

#### Scenario: 获取当前租户 ID
- **GIVEN** 已设置租户上下文，tenant_id = "tenant-123"
- **WHEN** 调用 `TenantContext.get_tenant_id()`
- **THEN** 返回 `"tenant-123"`

#### Scenario: 未设置租户时获取 ID
- **GIVEN** 未设置租户上下文
- **WHEN** 调用 `TenantContext.get_tenant_id()`
- **THEN** 返回 `None`

#### Scenario: 获取当前租户完整信息
- **GIVEN** 已设置租户上下文
- **WHEN** 调用 `TenantContext.get_current_tenant()`
- **THEN** 返回 SimpleTenant 对象，包含 id、name、code、status 等属性

#### Scenario: 获取数据库配置
- **GIVEN** 已设置租户上下文且配置了物理隔离数据库
- **WHEN** 调用 `TenantContext.get_database_config()`
- **THEN** 返回 TenantDatabaseConfig 对象，包含 host、port、database 等属性

#### Scenario: 请求结束后清理上下文
- **GIVEN** 已设置租户上下文
- **WHEN** 请求处理完成
- **THEN** TenantContext 被清理，get_tenant_id() 返回 None

