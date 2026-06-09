## ADDED Requirements

### 需求:模块管理

系统必须支持模块的创建、查询、更新和删除，模块是功能单元的模板定义。

#### 场景:创建模块
- **当** 管理员请求 `POST /api/v1/tenant/modules` 并提供 code、name
- **那么** 创建模块记录，返回模块信息；code 必须唯一

#### 场景:查询模块列表
- **当** 管理员请求 `GET /api/v1/tenant/modules`
- **那么** 返回所有模块列表，支持分页

#### 场景:获取模块详情
- **当** 管理员请求 `GET /api/v1/tenant/modules/{id}`
- **那么** 返回模块详细信息，包含 code、name、version、is_active、is_need

#### 场景:更新模块
- **当** 管理员请求 `PUT /api/v1/tenant/modules/{id}` 并提供更新数据
- **那么** 更新模块信息

#### 场景:删除模块
- **当** 管理员请求 `DELETE /api/v1/tenant/modules/{id}` 且该模块未被任何租户分配
- **那么** 删除模块及其下属菜单、权限、角色定义

#### 场景:删除已分配模块
- **当** 管理员尝试删除已被租户分配的模块
- **那么** 返回 HTTP 400，错误消息为"模块已被租户使用，禁止删除"

### 需求:模块菜单管理

系统必须支持模块菜单的树形结构定义，菜单通过 parent_id 构建层级关系。

#### 场景:创建模块菜单
- **当** 管理员请求 `POST /api/v1/tenant/modules/{id}/menus` 并提供 code、name、path
- **那么** 创建模块菜单记录；code 格式为 `module:name`，必须唯一

#### 场景:查询模块菜单树
- **当** 管理员请求 `GET /api/v1/tenant/modules/{id}/menus`
- **那么** 返回树形结构的菜单列表

#### 场景:更新模块菜单
- **当** 管理员请求 `PUT /api/v1/tenant/modules/{id}/menus/{menuId}`
- **那么** 更新菜单信息；变更触发 ModuleMenuUpdated 事件

#### 场景:删除模块菜单
- **当** 管理员请求 `DELETE /api/v1/tenant/modules/{id}/menus/{menuId}` 且该菜单无子菜单
- **那么** 删除菜单；触发 ModuleMenuDeleted 事件，同步删除租户实例层对应菜单

#### 场景:删除有子菜单的菜单
- **当** 管理员尝试删除有子菜单的菜单
- **那么** 返回 HTTP 400，错误消息为"存在子菜单，禁止删除"

### 需求:模块权限管理

系统必须支持模块权限定义，权限编码格式为 `module:resource:action`。

#### 场景:创建模块权限
- **当** 管理员请求 `POST /api/v1/tenant/modules/{id}/permissions` 并提供 code、name、resource、action
- **那么** 创建模块权限记录；code 必须唯一

#### 场景:查询模块权限列表
- **当** 管理员请求 `GET /api/v1/tenant/modules/{id}/permissions`
- **那么** 返回该模块的权限列表

#### 场景:更新模块权限
- **当** 管理员请求 `PUT /api/v1/tenant/modules/{id}/permissions/{permId}`
- **那么** 更新权限信息；触发 ModulePermissionUpdated 事件

#### 场景:删除模块权限
- **当** 管理员请求 `DELETE /api/v1/tenant/modules/{id}/permissions/{permId}`
- **那么** 删除权限及关联的 ModuleRolePermission；触发 ModulePermissionDeleted 事件

### 需求:模块角色管理

系统必须支持模块角色定义，每个模块必须包含两个系统角色（管理员和普通用户）。

#### 场景:创建模块角色
- **当** 管理员请求 `POST /api/v1/tenant/modules/{id}/roles` 并提供 code、name
- **那么** 创建模块角色记录；(module_id, code) 必须唯一

#### 场景:查询模块角色列表
- **当** 管理员请求 `GET /api/v1/tenant/modules/{id}/roles`
- **那么** 返回该模块的角色列表

#### 场景:更新非系统角色
- **当** 管理员请求 `PUT /api/v1/tenant/modules/{id}/roles/{roleId}` 且角色 is_system=false
- **那么** 更新角色信息；触发 ModuleRoleUpdated 事件

#### 场景:修改系统角色
- **当** 管理员尝试修改 is_system=true 的角色
- **那么** 返回 HTTP 400，错误消息为"系统内置角色禁止修改"

#### 场景:删除非系统角色
- **当** 管理员请求 `DELETE /api/v1/tenant/modules/{id}/roles/{roleId}` 且角色 is_system=false
- **那么** 删除角色及关联；触发 ModuleRoleDeleted 事件

#### 场景:删除系统角色
- **当** 管理员尝试删除 is_system=true 的角色
- **那么** 返回 HTTP 400，错误消息为"系统内置角色禁止删除"

### 需求:模块角色权限关联

系统必须支持为模块角色分配权限。

#### 场景:更新角色权限列表
- **当** 管理员请求 `PUT /api/v1/tenant/modules/{id}/roles/{roleId}/permissions` 并提供权限 ID 列表
- **那么** 整体替换该角色的权限关联；触发 ModuleRolePermissionChanged 事件

### 需求:模块默认角色自动创建

系统必须在创建模块时自动生成两个系统角色。

#### 场景:创建模块自动生成角色
- **当** 创建新模块
- **那么** 自动创建"系统管理员"角色（is_system=true，全权限）和"普通用户"角色（is_system=true，只读权限）
