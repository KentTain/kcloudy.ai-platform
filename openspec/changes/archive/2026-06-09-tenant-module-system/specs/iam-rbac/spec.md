## MODIFIED Requirements

### Requirement: 角色管理
系统 SHALL 支持角色的创建、查询、更新和删除。角色通过 ref_id 关联模块定义层的 ModuleRole，由同步机制创建。

#### Scenario: 创建角色
- **WHEN** 系统管理员请求 `POST /api/v1/iam/roles` 并提供角色编码和名称
- **THEN** 创建角色并返回角色信息

#### Scenario: 查询角色列表
- **WHEN** 系统管理员请求 `GET /api/v1/iam/roles`
- **THEN** 返回当前租户下的角色列表，包含 ref_id 字段

#### Scenario: 更新角色
- **WHEN** 系统管理员请求 `PUT /api/v1/iam/roles/{id}` 并提供更新数据
- **THEN** 更新角色信息

#### Scenario: 删除自定义角色
- **WHEN** 系统管理员请求 `DELETE /api/v1/iam/roles/{id}` 且角色非系统内置
- **THEN** 删除角色

#### Scenario: 删除系统内置角色
- **WHEN** 系统管理员尝试删除系统内置角色（`is_system = true`）
- **THEN** 返回 HTTP 400，错误消息为"系统内置角色不可删除"

### Requirement: 权限管理
系统 SHALL 支持权限的定义和查询。权限通过 ref_id 关联模块定义层的 ModulePermission，由同步机制创建。

#### Scenario: 查询权限列表
- **WHEN** 系统管理员请求 `GET /api/v1/iam/permissions`
- **THEN** 返回所有权限列表，包含 ref_id 字段

#### Scenario: 权限命名规范
- **WHEN** 定义新权限
- **THEN** 权限编码格式为 `module:resource:action`（如 `iam:user:read`、`tenant:module:write`）

### Requirement: 角色 - 权限关联
系统 SHALL 支持为角色分配权限。RolePermission 记录包含 tenant_id 字段。

#### Scenario: 为角色分配权限
- **WHEN** 系统管理员请求 `POST /api/v1/iam/roles/{id}/permissions` 并提供权限 ID 列表
- **THEN** 创建角色 - 权限关联，包含 tenant_id

#### Scenario: 移除角色权限
- **WHEN** 系统管理员请求 `DELETE /api/v1/iam/roles/{id}/permissions/{permission_id}`
- **THEN** 删除角色 - 权限关联

#### Scenario: 查询角色权限
- **WHEN** 系统管理员请求 `GET /api/v1/iam/roles/{id}/permissions`
- **THEN** 返回该角色的所有权限列表

### Requirement: 用户 - 角色关联
系统 SHALL 支持为用户分配角色。UserRole 记录包含 tenant_id 字段。

#### Scenario: 为用户分配角色
- **WHEN** 系统管理员请求 `POST /api/v1/iam/users/{id}/roles` 并提供角色 ID 列表
- **THEN** 创建用户 - 角色关联，包含 tenant_id

#### Scenario: 移除用户角色
- **WHEN** 系统管理员请求 `DELETE /api/v1/iam/users/{id}/roles/{role_id}`
- **THEN** 删除用户 - 角色关联

#### Scenario: 查询用户角色
- **WHEN** 系统管理员请求 `GET /api/v1/iam/users/{id}/roles`
- **THEN** 返回该用户的所有角色列表
