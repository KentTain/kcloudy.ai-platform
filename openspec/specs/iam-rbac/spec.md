# IAM RBAC 规范

## Purpose

定义基于角色的访问控制 (RBAC) 权限模型，支持角色管理、权限管理和用户 - 角色关联。

## Requirements

### Requirement: 角色管理

系统 SHALL 支持角色的创建、查询、更新和删除。

#### Scenario: 创建角色
- **WHEN** 系统管理员请求 `POST /api/v1/iam/roles` 并提供角色编码和名称
- **THEN** 创建角色并返回角色信息

#### Scenario: 查询角色列表
- **WHEN** 系统管理员请求 `GET /api/v1/iam/roles`
- **THEN** 返回当前租户下的角色列表

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

系统 SHALL 支持权限的定义和查询。

#### Scenario: 查询权限列表
- **WHEN** 系统管理员请求 `GET /api/v1/iam/permissions`
- **THEN** 返回所有权限列表

#### Scenario: 权限命名规范
- **WHEN** 定义新权限
- **THEN** 权限编码格式为 `资源：操作`（如 `user:read`、`user:write`）

### Requirement: 角色 - 权限关联

系统 SHALL 支持为角色分配权限。

#### Scenario: 为角色分配权限
- **WHEN** 系统管理员请求 `POST /api/v1/iam/roles/{id}/permissions` 并提供权限 ID 列表
- **THEN** 创建角色 - 权限关联

#### Scenario: 移除角色权限
- **WHEN** 系统管理员请求 `DELETE /api/v1/iam/roles/{id}/permissions/{permission_id}`
- **THEN** 删除角色 - 权限关联

#### Scenario: 查询角色权限
- **WHEN** 系统管理员请求 `GET /api/v1/iam/roles/{id}/permissions`
- **THEN** 返回该角色的所有权限列表

### Requirement: 用户 - 角色关联

系统 SHALL 支持为用户分配角色。

#### Scenario: 为用户分配角色
- **WHEN** 系统管理员请求 `POST /api/v1/iam/users/{id}/roles` 并提供角色 ID 列表
- **THEN** 创建用户 - 角色关联

#### Scenario: 移除用户角色
- **WHEN** 系统管理员请求 `DELETE /api/v1/iam/users/{id}/roles/{role_id}`
- **THEN** 删除用户 - 角色关联

#### Scenario: 查询用户角色
- **WHEN** 系统管理员请求 `GET /api/v1/iam/users/{id}/roles`
- **THEN** 返回该用户的所有角色列表

### Requirement: 权限检查

系统 SHALL 提供权限检查机制。

#### Scenario: 用户拥有所需权限
- **WHEN** 用户访问需要 `user:read` 权限的接口
- **AND** 用户的角色包含 `user:read` 权限
- **THEN** 允许访问

#### Scenario: 用户缺少所需权限
- **WHEN** 用户访问需要 `user:delete` 权限的接口
- **AND** 用户的角色不包含 `user:delete` 权限
- **THEN** 返回 HTTP 403，错误消息为"权限不足"

#### Scenario: 通配符权限匹配
- **WHEN** 用户拥有 `user:*` 权限
- **THEN** 用户可访问所有 `user:` 前缀的权限接口

### Requirement: 预定义角色

系统 SHALL 提供预定义的系统角色。

#### Scenario: 系统初始化创建预定义角色
- **WHEN** 系统首次启动
- **THEN** 自动创建租户管理员、系统管理员、普通用户三个角色

#### Scenario: 租户管理员权限
- **WHEN** 用户角色为租户管理员
- **THEN** 拥有创建租户、管理系统管理员的权限

#### Scenario: 系统管理员权限
- **WHEN** 用户角色为系统管理员
- **THEN** 拥有管理本租户用户、角色、权限的权限

#### Scenario: 普通用户权限
- **WHEN** 用户角色为普通用户
- **THEN** 仅拥有基本业务功能权限

### Requirement: 租户隔离

系统 SHALL 确保角色和权限在租户内隔离。

#### Scenario: 查询角色仅返回本租户
- **WHEN** 系统管理员查询角色列表
- **THEN** 仅返回当前租户下的角色

#### Scenario: 角色编码租户内唯一
- **WHEN** 创建角色时编码与同租户已有角色重复
- **THEN** 返回 HTTP 400，错误消息为"角色编码已存在"

#### Scenario: 不同租户角色编码可相同
- **WHEN** 不同租户创建相同编码的角色
- **THEN** 允许创建

