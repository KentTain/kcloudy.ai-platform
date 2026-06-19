## ADDED Requirements

### 需求:ModuleAssigned 事件处理

IAM 模块必须监听 ModuleAssigned 事件，为租户创建完整的菜单、权限、角色实例。

#### 场景:模块分配时同步创建租户实例
- **当** 收到 ModuleAssigned 事件
- **那么** 查询模块的所有菜单、权限、角色
- **且** 为该租户创建 Menu、Permission、Role 记录（ref_id 关联模块定义）
- **且** 创建 RolePermission 关联
- **且** 按 parent_id 重建菜单树结构

#### 场景:模块分配时同步默认角色权限
- **当** 收到 ModuleAssigned 事件
- **那么** 系统管理员角色自动关联模块所有权限
- **且** 普通用户角色仅关联 read 操作权限

### 需求:ModuleUnassigned 事件处理

IAM 模块必须监听 ModuleUnassigned 事件，级联删除租户实例层数据。

#### 场景:模块取消分配时级联删除
- **当** 收到 ModuleUnassigned 事件
- **那么** 按依赖顺序删除：RolePermission → Role → Permission → Menu
- **且** 删除该租户所有 ref_id 指向该模块的记录

### 需求:ModuleMenuCreated 事件处理

IAM 模块必须监听 ModuleMenuCreated 事件，为所有已分配该模块的租户创建菜单。

#### 场景:新增菜单同步
- **当** 收到 ModuleMenuCreated 事件
- **那么** 遍历所有已分配该模块的租户
- **且** 为每个租户创建 Menu 记录，ref_id = module_menu_id
- **且** 根据 module_menu.parent_id 找到对应的租户菜单 parent_id

### 需求:ModuleMenuUpdated 事件处理

IAM 模块必须监听 ModuleMenuUpdated 事件，同步更新租户菜单信息。

#### 场景:菜单更新同步
- **当** 收到 ModuleMenuUpdated 事件
- **那么** 遍历所有已分配该模块的租户
- **且** 更新 ref_id 匹配的 Menu 记录（name、path、icon、sort_order、is_visible）

### 需求:ModuleMenuDeleted 事件处理

IAM 模块必须监听 ModuleMenuDeleted 事件，同步删除租户菜单。

#### 场景:菜单删除同步
- **当** 收到 ModuleMenuDeleted 事件
- **那么** 遍历所有已分配该模块的租户
- **且** 删除 ref_id 匹配的 Menu 记录
- **且** 级联删除子菜单

### 需求:ModulePermissionCreated 事件处理

IAM 模块必须监听 ModulePermissionCreated 事件，为所有已分配该模块的租户创建权限。

#### 场景:新增权限同步
- **当** 收到 ModulePermissionCreated 事件
- **那么** 为所有已分配该模块的租户创建 Permission 记录

#### 场景:新增权限同步到系统管理员角色
- **当** 新增权限同步到租户
- **那么** 如果是 write/delete 操作，自动关联到系统管理员角色
- **且** 如果是 read 操作，同时关联到系统管理员和普通用户角色

### 需求:ModulePermissionUpdated 事件处理

IAM 模块必须监听 ModulePermissionUpdated 事件，同步更新租户权限。

#### 场景:权限更新同步
- **当** 收到 ModulePermissionUpdated 事件
- **那么** 更新 ref_id 匹配的 Permission 记录

### 需求:ModulePermissionDeleted 事件处理

IAM 模块必须监听 ModulePermissionDeleted 事件，同步删除租户权限及关联。

#### 场景:权限删除同步
- **当** 收到 ModulePermissionDeleted 事件
- **那么** 删除 ref_id 匹配的 Permission 记录
- **且** 级联删除 RolePermission 关联

### 需求:ModuleRoleCreated 事件处理

IAM 模块必须监听 ModuleRoleCreated 事件，为所有已分配该模块的租户创建角色。

#### 场景:新增角色同步
- **当** 收到 ModuleRoleCreated 事件
- **那么** 为所有已分配该模块的租户创建 Role 记录

### 需求:ModuleRoleUpdated 事件处理

IAM 模块必须监听 ModuleRoleUpdated 事件，同步更新租户角色信息。

#### 场景:角色更新同步
- **当** 收到 ModuleRoleUpdated 事件
- **那么** 更新 ref_id 匹配的 Role 记录（name、description）

### 需求:ModuleRoleDeleted 事件处理

IAM 模块必须监听 ModuleRoleDeleted 事件，同步删除租户角色及关联。

#### 场景:角色删除同步
- **当** 收到 ModuleRoleDeleted 事件
- **那么** 删除 ref_id 匹配的 Role 记录
- **且** 级联删除 RolePermission 关联
- **且** 级联删除 UserRole 关联

### 需求:ModuleRolePermissionChanged 事件处理

IAM 模块必须监听 ModuleRolePermissionChanged 事件，同步更新租户角色的权限关联。

#### 场景:角色权限变更同步
- **当** 收到 ModuleRolePermissionChanged 事件
- **那么** 遍历所有已分配该模块的租户
- **且** 根据 ref_id 找到对应的租户角色和权限
- **且** 整体替换该角色的 RolePermission 关联

### 需求:租户实例层只读访问

租户实例层的菜单、权限、角色数据必须由同步机制维护，租户管理员只能查询。

#### 场景:查询租户菜单树
- **当** 管理员请求 `GET /api/v1/iam/tenants/{tenantId}/menus`
- **那么** 返回该租户的菜单树

#### 场景:查询租户权限列表
- **当** 管理员请求 `GET /api/v1/iam/tenants/{tenantId}/permissions`
- **那么** 返回该租户的权限列表

#### 场景:查询租户角色列表
- **当** 管理员请求 `GET /api/v1/iam/tenants/{tenantId}/roles`
- **那么** 返回该租户的角色列表

#### 场景:查询角色详情含权限
- **当** 管理员请求 `GET /api/v1/iam/tenants/{tenantId}/roles/{roleId}`
- **那么** 返回角色详情及其权限列表
