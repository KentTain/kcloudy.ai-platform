## ADDED Requirements

### Requirement: 后端权限检查中间件

系统 SHALL 提供后端权限检查中间件。

#### Scenario: 接口权限拦截
- **WHEN** 用户访问需要特定权限的 API 接口
- **THEN** 中间件检查用户是否拥有所需权限

#### Scenario: 权限不足返回 403
- **WHEN** 用户缺少访问接口所需的权限
- **THEN** 返回 HTTP 403，错误消息为"权限不足"

#### Scenario: Token 解析获取权限
- **WHEN** 请求携带有效 Token
- **THEN** 从 Token 中提取用户权限列表

### Requirement: 权限缓存

系统 SHALL 缓存用户权限信息以提高性能。

#### Scenario: 权限缓存到 Redis
- **WHEN** 用户登录成功
- **THEN** 将用户权限列表缓存到 Redis，TTL 为 5 分钟

#### Scenario: 权限变更清除缓存
- **WHEN** 用户角色或权限发生变更
- **THEN** 清除该用户的权限缓存

#### Scenario: 权限缓存命中
- **WHEN** 检查用户权限时缓存存在
- **THEN** 直接从缓存读取权限列表

### Requirement: 权限装饰器

系统 SHALL 提供权限检查装饰器。

#### Scenario: 使用装饰器保护接口
- **WHEN** 控制器方法使用 `@require_permission("user:read")` 装饰器
- **THEN** 访问该方法前检查用户是否拥有 `user:read` 权限

#### Scenario: 多权限任一满足
- **WHEN** 装饰器指定多个权限 `@require_permission(["user:read", "user:write"])`
- **THEN** 用户拥有任一权限即可访问
