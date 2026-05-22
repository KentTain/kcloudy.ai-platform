# role-permission-hierarchy Specification

## Purpose
TBD - created by archiving change complete-iam-multi-tenancy. Update Purpose after archive.
## Requirements
### Requirement: 三级角色体系定义

系统 SHALL 实现租户管理员、系统管理员、普通用户三级角色体系，每级角色有明确的职责范围。

#### Scenario: 租户管理员职责
- **GIVEN** 用户拥有租户管理员角色
- **WHEN** 该用户登录管理后台 /admin/
- **THEN** 可以创建和管理本租户的系统管理员账户
- **AND** 可以管理租户配置（但不能删除自己的租户管理员身份）

#### Scenario: 系统管理员职责
- **GIVEN** 用户拥有系统管理员角色（属于某租户）
- **WHEN** 该用户登录控制台 /console/
- **AND** 在该租户上下文中操作
- **THEN** 可以管理本租户的用户、角色、权限
- **AND** 可以管理本租户的部门、组织架构
- **AND** 不能管理其他租户的数据

#### Scenario: 普通用户职责
- **GIVEN** 用户拥有普通用户角色（属于某租户）
- **WHEN** 该用户登录控制台 /console/
- **AND** 在该租户上下文中操作
- **THEN** 只能使用业务功能（如查看/编辑自己的数据集）
- **AND** 不能访问管理功能

---

### Requirement: 角色权限继承

系统 SHALL 实现角色间的权限继承，子角色自动拥有父角色的权限。

#### Scenario: 系统管理员继承普通用户权限
- **GIVEN** 系统管理员角色关联了 user:read、user:write、role:read 等权限
- **AND** 普通用户角色关联了 user:read 权限
- **WHEN** 检查系统管理员是否拥有 user:read 权限
- **THEN** 返回 True（继承自普通用户角色）

#### Scenario: 租户管理员拥有所有权限
- **GIVEN** 租户管理员角色是最高权限角色
- **WHEN** 检查租户管理员是否拥有任意权限
- **THEN** 返回 True（租户管理员拥有所有权限的通配符）

---

### Requirement: 租户管理员登录认证

系统 SHALL 为租户管理员提供独立的登录入口和认证机制。

#### Scene: 租户管理员登录
- **GIVEN** 租户管理员用户名 "admin"，密码 "admin123"
- **WHEN** 该管理员 POST /admin/v1/auth/login
- **THEN** 系统验证用户名和密码
- **AND** 返回包含 token 的响应

#### Scenario: 租户管理员密码错误
- **GIVEN** 租户管理员用户名正确但密码错误
- **WHEN** 该管理员 POST /admin/v1/auth/login
- **THEN** 系统返回 HTTP 401 错误，消息为 "用户名或密码错误"

#### Scenario: 租户管理员 Token 验证
- **GIVEN** 租户管理员已登录并获取 token
- **WHEN** 该管理员携带 Token 访问 /admin/v1/tenants
- **THEN** 中间件验证 Token 有效后放行
- **AND** 在 request.state.admin 中注入管理员信息

---

### Requirement: 用户登录时关联租户

系统 SHALL 在用户登录时通过 JWT Token 携带用户的默认租户信息。

#### Scenario: 用户登录返回租户信息
- **GIVEN** 用户 "user1" 属于租户 "tenant-123"，并设置该租户为默认
- **WHEN** 用户 POST /api/v1/iam/auth/login 登录
- **THEN** 系统返回 access_token
- **AND** Token payload 包含 tenant_id: "tenant-123"

#### Scenario: 用户切换租户
- **GIVEN** 用户属于多个租户
- **WHEN** 用户 POST /console/v1/tenants/{tenant_id}/switch
- **THEN** 系统返回新的 token，其中 tenant_id 更新为切换后的租户

