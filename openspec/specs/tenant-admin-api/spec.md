## ADDED Requirements

### Requirement: 独立认证体系

系统 SHALL 为管理后台提供独立的超级管理员认证体系。

#### Scenario: 管理员登录
- **WHEN** 超级管理员使用正确的用户名和密码登录
- **THEN** 返回管理员 Token

#### Scenario: 非管理员访问被拒绝
- **WHEN** 普通用户尝试访问管理后台 API
- **THEN** 返回 HTTP 403 错误

#### Scenario: 无 Token 访问被拒绝
- **WHEN** 未携带 Token 访问管理后台 API
- **THEN** 返回 HTTP 401 错误

### Requirement: BCrypt 密码存储

系统 SHALL 使用 BCrypt 算法存储租户管理员密码哈希。

#### Scenario: 密码哈希存储
- **WHEN** 创建或修改租户管理员密码
- **THEN** 使用 BCrypt（cost factor = 12）计算哈希值并存储

#### Scenario: 密码验证
- **WHEN** 租户管理员登录时验证密码
- **THEN** 使用 BCrypt 比对输入密码与存储的哈希值

### Requirement: 租户列表查询

系统 SHALL 支持跨租户查询租户列表。

#### Scenario: 查询租户列表
- **WHEN** 管理员请求 `GET /admin/v1/tenants`
- **THEN** 返回所有租户列表（分页）

#### Scenario: 搜索租户
- **WHEN** 管理员请求 `GET /admin/v1/tenants?keyword=acme`
- **THEN** 返回名称或编码包含 "acme" 的租户列表

### Requirement: 租户创建

系统 SHALL 支持创建新租户。

#### Scenario: 创建租户
- **WHEN** 管理员请求 `POST /admin/v1/tenants` 并提供名称、编码
- **THEN** 创建新租户并返回租户信息

#### Scenario: 创建重复编码租户
- **WHEN** 管理员尝试创建已存在编码的租户
- **THEN** 返回 HTTP 400 错误，消息为 "租户编码已存在"

### Requirement: 租户详情查询

系统 SHALL 支持查询租户详情。

#### Scenario: 查询租户详情
- **WHEN** 管理员请求 `GET /admin/v1/tenants/{id}`
- **THEN** 返回租户详细信息

#### Scenario: 查询不存在的租户
- **WHEN** 管理员请求 `GET /admin/v1/tenants/nonexistent`
- **THEN** 返回 HTTP 404 错误

### Requirement: 租户更新

系统 SHALL 支持更新租户信息。

#### Scenario: 更新租户
- **WHEN** 管理员请求 `PUT /admin/v1/tenants/{id}` 并提供更新数据
- **THEN** 更新租户信息并返回更新后的数据

### Requirement: 租户删除

系统 SHALL 支持删除租户。

#### Scenario: 删除租户
- **WHEN** 管理员请求 `DELETE /admin/v1/tenants/{id}`
- **THEN** 删除租户（软删除）

#### Scenario: 删除有用户的租户
- **WHEN** 管理员尝试删除有用户关联的租户
- **THEN** 返回 HTTP 400 错误，消息为 "租户下存在用户，无法删除"

### Requirement: 租户激活

系统 SHALL 支持激活租户。

#### Scenario: 激活租户
- **WHEN** 管理员请求 `POST /admin/v1/tenants/{id}/activate`
- **THEN** 租户状态变为 `active`

### Requirement: 租户停用

系统 SHALL 支持停用租户。

#### Scenario: 停用租户
- **WHEN** 管理员请求 `POST /admin/v1/tenants/{id}/deactivate`
- **THEN** 租户状态变为 `inactive`

### Requirement: 租户统计

系统 SHALL 支持查询租户统计信息。

#### Scenario: 查询租户统计
- **WHEN** 管理员请求 `GET /admin/v1/tenants/{id}/stats`
- **THEN** 返回租户统计信息（用户数、存储用量等）

### Requirement: 默认租户管理员初始化

系统 SHALL 在启动时自动创建默认租户管理员。

#### Scenario: 首次启动创建默认管理员
- **WHEN** 系统首次启动且不存在默认租户管理员
- **THEN** 自动创建默认租户管理员

#### Scenario: 已存在默认管理员时跳过
- **WHEN** 系统启动时已存在默认租户管理员
- **THEN** 跳过创建
