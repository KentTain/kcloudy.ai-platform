# IAM Admin API 规范

## Purpose

定义 IAM 管理后台 API，提供用户、角色、权限、部门、菜单的管理接口，用于系统管理员进行身份与权限管理。
## Requirements
### 需求: 管理后台用户 API

系统 SHALL 在 `/admin/v1/iam/users` 路径下提供用户管理接口，包括用户列表、创建、详情、更新、删除、状态管理、密码重置、角色分配、部门分配。

**变更说明**：响应构建使用 Schema `from_entity()` 方法，替代手动字典组装。

#### 场景: 获取用户列表
- **当** 管理员发送 GET /admin/v1/iam/users
- **那么** 系统返回分页用户列表

#### 场景: 创建用户
- **当** 管理员发送 POST /admin/v1/iam/users 包含用户信息
- **那么** 系统创建用户并返回用户详情

#### 场景: 获取用户详情
- **当** 管理员发送 GET /admin/v1/iam/users/{id}
- **那么** 系统返回指定用户详情

#### 场景: 更新用户
- **当** 管理员发送 PUT /admin/v1/iam/users/{id} 包含更新信息
- **那么** 系统更新用户并返回更新后详情

#### 场景: 删除用户
- **当** 管理员发送 DELETE /admin/v1/iam/users/{id}
- **那么** 系统软删除用户

#### 场景: 启用用户
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/enable
- **那么** 系统将用户状态设为 active

#### 场景: 停用用户
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/disable
- **那么** 系统将用户状态设为 inactive

#### 场景: 锁定用户
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/lock
- **那么** 系统将用户状态设为 locked

#### 场景: 更新用户状态
- **当** 管理员发送 PUT /admin/v1/iam/users/{id}/status 包含目标状态
- **那么** 系统将用户状态设为指定值

#### 场景: 重置用户密码
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/reset-password
- **那么** 系统重置密码并返回新密码

#### 场景: 获取用户角色（修改）
- **当** 管理员发送 GET /admin/v1/iam/users/{id}/roles
- **那么** 系统使用 `UserRolesResponse.from_roles()` 返回用户已分配的角色列表

#### 场景: 分配用户角色
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/roles 包含角色 ID 列表
- **那么** 系统覆盖式分配角色

#### 场景: 获取用户部门
- **当** 管理员发送 GET /admin/v1/iam/users/{id}/departments
- **那么** 系统返回用户所属部门列表

#### 场景: 分配用户部门
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/departments 包含部门 ID 列表
- **那么** 系统覆盖式分配部门

### Requirement: 管理后台角色 API

系统 SHALL 在 `/admin/v1/iam/roles` 路径下提供角色管理接口。

#### Scenario: 获取角色列表
- **WHEN** 管理员发送 GET /admin/v1/iam/roles
- **THEN** 系统返回分页角色列表

#### Scenario: 创建角色
- **WHEN** 管理员发送 POST /admin/v1/iam/roles 包含角色信息
- **THEN** 系统创建角色并返回角色详情

#### Scenario: 获取角色详情
- **WHEN** 管理员发送 GET /admin/v1/iam/roles/{id}
- **THEN** 系统返回指定角色详情

#### Scenario: 更新角色
- **WHEN** 管理员发送 PUT /admin/v1/iam/roles/{id} 包含更新信息
- **THEN** 系统更新角色并返回更新后详情

#### Scenario: 删除角色
- **WHEN** 管理员发送 DELETE /admin/v1/iam/roles/{id}
- **THEN** 系统删除角色

#### Scenario: 获取角色权限
- **WHEN** 管理员发送 GET /admin/v1/iam/roles/{id}/permissions
- **THEN** 系统返回角色的权限列表

#### Scenario: 分配角色权限
- **WHEN** 管理员发送 POST /admin/v1/iam/roles/{id}/permissions 包含权限 ID 列表
- **THEN** 系统覆盖式分配权限

### Requirement: 管理后台权限 API

系统 SHALL 在 `/admin/v1/iam/permissions` 路径下提供权限查询接口。

#### Scenario: 获取权限列表
- **WHEN** 管理员发送 GET /admin/v1/iam/permissions
- **THEN** 系统返回所有权限列表

#### Scenario: 获取分组权限
- **WHEN** 管理员发送 GET /admin/v1/iam/permissions/grouped
- **THEN** 系统返回按资源分组的权限

### 需求: 管理后台部门 API

系统 SHALL 在 `/admin/v1/iam/departments` 路径下提供部门管理接口。

**变更说明**：响应构建使用 Schema `from_entity()` 方法，替代手动字典组装。

#### 场景: 获取部门列表（修改）
- **当** 管理员发送 GET /admin/v1/iam/departments
- **那么** 系统使用 `DepartmentListResponse.from_departments()` 返回当前租户的部门列表

#### 场景: 获取部门树
- **当** 管理员发送 GET /admin/v1/iam/departments/tree
- **那么** 系统返回部门树形结构

#### 场景: 创建部门
- **当** 管理员发送 POST /admin/v1/iam/departments 包含部门信息
- **那么** 系统创建部门并返回部门信息

#### 场景: 更新部门
- **当** 管理员发送 PUT /admin/v1/iam/departments/{id} 包含更新信息
- **那么** 系统更新部门

#### 场景: 删除部门
- **当** 管理员发送 DELETE /admin/v1/iam/departments/{id}
- **那么** 系统删除部门

#### 场景: 获取部门用户
- **当** 管理员发送 GET /admin/v1/iam/departments/{id}/users
- **那么** 系统返回部门下的用户列表

#### 场景: 添加用户到部门
- **当** 管理员发送 POST /admin/v1/iam/departments/{id}/users 包含用户信息
- **那么** 系统将用户添加到部门

#### 场景: 从部门移除用户
- **当** 管理员发送 DELETE /admin/v1/iam/departments/{id}/users/{uid}
- **那么** 系统将用户从部门移除

### Requirement: 管理后台菜单 API

系统 SHALL 在 `/admin/v1/iam/menus` 路径下提供菜单查询接口。

#### Scenario: 获取所有菜单
- **WHEN** 管理员发送 GET /admin/v1/iam/menus
- **THEN** 系统返回所有菜单的树形结构

### 需求: 用户角色列表响应 Schema

系统 SHALL 提供 `UserRolesResponse` 和 `UserRoleItem` Schema，用于用户角色列表响应。

#### 场景: UserRoleItem 字段完整性
- **当** 构建 `UserRoleItem` 时
- **那么** 必须包含 id、code、name、description 字段

#### 场景: from_role() 转换方法
- **当** 调用 `UserRoleItem.from_role(role)`
- **那么** 返回包含角色信息的 `UserRoleItem` 对象

#### 场景: UserRolesResponse.from_roles() 转换方法
- **当** 调用 `UserRolesResponse.from_roles(roles)`
- **那么** 返回包含角色列表的 `UserRolesResponse` 对象

### 需求: 部门列表响应 Schema

系统 SHALL 提供 `DepartmentListResponse` 和 `DepartmentListItem` Schema，用于部门列表响应。

#### 场景: DepartmentListItem 字段完整性
- **当** 构建 `DepartmentListItem` 时
- **那么** 必须包含 id、name、code、parent_id、sort_order、leader_id、status 字段

#### 场景: from_department() 转换方法
- **当** 调用 `DepartmentListItem.from_department(department)`
- **那么** 返回包含部门信息的 `DepartmentListItem` 对象

#### 场景: DepartmentListResponse.from_departments() 转换方法
- **当** 调用 `DepartmentListResponse.from_departments(departments)`
- **那么** 返回包含部门列表的 `DepartmentListResponse` 对象

