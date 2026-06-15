## 新增需求

### 需求:管理后台用户 API
系统必须在 `/admin/v1/iam/users` 路径下提供用户管理接口，包括用户列表、创建、详情、更新、删除、状态管理、密码重置、角色分配、部门分配。

#### 场景:获取用户列表
- **当** 管理员发送 GET /admin/v1/iam/users
- **那么** 系统返回分页用户列表

#### 场景:创建用户
- **当** 管理员发送 POST /admin/v1/iam/users 包含用户信息
- **那么** 系统创建用户并返回用户详情

#### 场景:获取用户详情
- **当** 管理员发送 GET /admin/v1/iam/users/{id}
- **那么** 系统返回指定用户详情

#### 场景:更新用户
- **当** 管理员发送 PUT /admin/v1/iam/users/{id} 包含更新信息
- **那么** 系统更新用户并返回更新后详情

#### 场景:删除用户
- **当** 管理员发送 DELETE /admin/v1/iam/users/{id}
- **那么** 系统软删除用户

#### 场景:启用用户
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/enable
- **那么** 系统将用户状态设为 active

#### 场景:停用用户
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/disable
- **那么** 系统将用户状态设为 inactive

#### 场景:锁定用户
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/lock
- **那么** 系统将用户状态设为 locked

#### 场景:更新用户状态
- **当** 管理员发送 PUT /admin/v1/iam/users/{id}/status 包含目标状态
- **那么** 系统将用户状态设为指定值

#### 场景:重置用户密码
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/reset-password
- **那么** 系统重置密码并返回新密码

#### 场景:获取用户角色
- **当** 管理员发送 GET /admin/v1/iam/users/{id}/roles
- **那么** 系统返回用户已分配的角色列表

#### 场景:分配用户角色
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/roles 包含角色 ID 列表
- **那么** 系统覆盖式分配角色

#### 场景:获取用户部门
- **当** 管理员发送 GET /admin/v1/iam/users/{id}/departments
- **那么** 系统返回用户所属部门列表

#### 场景:分配用户部门
- **当** 管理员发送 POST /admin/v1/iam/users/{id}/departments 包含部门 ID 列表
- **那么** 系统覆盖式分配部门

### 需求:管理后台角色 API
系统必须在 `/admin/v1/iam/roles` 路径下提供角色管理接口。

#### 场景:获取角色列表
- **当** 管理员发送 GET /admin/v1/iam/roles
- **那么** 系统返回分页角色列表

#### 场景:创建角色
- **当** 管理员发送 POST /admin/v1/iam/roles 包含角色信息
- **那么** 系统创建角色并返回角色详情

#### 场景:获取角色详情
- **当** 管理员发送 GET /admin/v1/iam/roles/{id}
- **那么** 系统返回指定角色详情

#### 场景:更新角色
- **当** 管理员发送 PUT /admin/v1/iam/roles/{id} 包含更新信息
- **那么** 系统更新角色并返回更新后详情

#### 场景:删除角色
- **当** 管理员发送 DELETE /admin/v1/iam/roles/{id}
- **那么** 系统删除角色

#### 场景:获取角色权限
- **当** 管理员发送 GET /admin/v1/iam/roles/{id}/permissions
- **那么** 系统返回角色的权限列表

#### 场景:分配角色权限
- **当** 管理员发送 POST /admin/v1/iam/roles/{id}/permissions 包含权限 ID 列表
- **那么** 系统覆盖式分配权限

### 需求:管理后台权限 API
系统必须在 `/admin/v1/iam/permissions` 路径下提供权限查询接口。

#### 场景:获取权限列表
- **当** 管理员发送 GET /admin/v1/iam/permissions
- **那么** 系统返回所有权限列表

#### 场景:获取分组权限
- **当** 管理员发送 GET /admin/v1/iam/permissions/grouped
- **那么** 系统返回按资源分组的权限

### 需求:管理后台部门 API
系统必须在 `/admin/v1/iam/departments` 路径下提供部门管理接口。

#### 场景:获取部门列表
- **当** 管理员发送 GET /admin/v1/iam/departments
- **那么** 系统返回当前租户的部门列表

#### 场景:获取部门树
- **当** 管理员发送 GET /admin/v1/iam/departments/tree
- **那么** 系统返回部门树形结构

#### 场景:创建部门
- **当** 管理员发送 POST /admin/v1/iam/departments 包含部门信息
- **那么** 系统创建部门并返回部门信息

#### 场景:更新部门
- **当** 管理员发送 PUT /admin/v1/iam/departments/{id} 包含更新信息
- **那么** 系统更新部门

#### 场景:删除部门
- **当** 管理员发送 DELETE /admin/v1/iam/departments/{id}
- **那么** 系统删除部门

#### 场景:获取部门用户
- **当** 管理员发送 GET /admin/v1/iam/departments/{id}/users
- **那么** 系统返回部门下的用户列表

#### 场景:添加用户到部门
- **当** 管理员发送 POST /admin/v1/iam/departments/{id}/users 包含用户信息
- **那么** 系统将用户添加到部门

#### 场景:从部门移除用户
- **当** 管理员发送 DELETE /admin/v1/iam/departments/{id}/users/{uid}
- **那么** 系统将用户从部门移除

### 需求:管理后台菜单 API
系统必须在 `/admin/v1/iam/menus` 路径下提供菜单查询接口。

#### 场景:获取所有菜单
- **当** 管理员发送 GET /admin/v1/iam/menus
- **那么** 系统返回所有菜单的树形结构
