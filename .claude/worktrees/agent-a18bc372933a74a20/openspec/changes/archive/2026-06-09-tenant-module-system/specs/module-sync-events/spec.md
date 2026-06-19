## ADDED Requirements

### 需求:模块分配事件

系统必须在租户分配模块时发布 ModuleAssigned 事件。

#### 场景:发布 ModuleAssigned 事件
- **当** 租户成功分配模块
- **那么** 发布 ModuleAssigned 事件，携带 tenant_id 和 module_id

### 需求:模块取消分配事件

系统必须在租户取消模块分配时发布 ModuleUnassigned 事件。

#### 场景:发布 ModuleUnassigned 事件
- **当** 租户成功取消模块分配
- **那么** 发布 ModuleUnassigned 事件，携带 tenant_id 和 module_id

### 需求:模块菜单变更事件

系统必须在模块菜单发生增删改时发布对应事件。

#### 场景:发布 ModuleMenuCreated 事件
- **当** 模块新增菜单
- **那么** 发布 ModuleMenuCreated 事件，携带 module_menu_id

#### 场景:发布 ModuleMenuUpdated 事件
- **当** 模块菜单更新
- **那么** 发布 ModuleMenuUpdated 事件，携带 module_menu_id

#### 场景:发布 ModuleMenuDeleted 事件
- **当** 模块菜单删除
- **那么** 发布 ModuleMenuDeleted 事件，携带 module_id 和 menu_code

### 需求:模块权限变更事件

系统必须在模块权限发生增删改时发布对应事件。

#### 场景:发布 ModulePermissionCreated 事件
- **当** 模块新增权限
- **那么** 发布 ModulePermissionCreated 事件，携带 module_permission_id

#### 场景:发布 ModulePermissionUpdated 事件
- **当** 模块权限更新
- **那么** 发布 ModulePermissionUpdated 事件，携带 module_permission_id

#### 场景:发布 ModulePermissionDeleted 事件
- **当** 模块权限删除
- **那么** 发布 ModulePermissionDeleted 事件，携带 module_id 和 permission_code

### 需求:模块角色变更事件

系统必须在模块角色发生增删改时发布对应事件。

#### 场景:发布 ModuleRoleCreated 事件
- **当** 模块新增角色
- **那么** 发布 ModuleRoleCreated 事件，携带 module_role_id

#### 场景:发布 ModuleRoleUpdated 事件
- **当** 模块角色更新
- **那么** 发布 ModuleRoleUpdated 事件，携带 module_role_id

#### 场景:发布 ModuleRoleDeleted 事件
- **当** 模块角色删除
- **那么** 发布 ModuleRoleDeleted 事件，携带 module_id 和 role_code

### 需求:模块角色权限变更事件

系统必须在模块角色权限关联变更时发布事件。

#### 场景:发布 ModuleRolePermissionChanged 事件
- **当** 模块角色的权限列表更新
- **那么** 发布 ModuleRolePermissionChanged 事件，携带 module_role_id

### 需求:事件可靠性

系统必须确保领域事件的可靠传递。

#### 场景:事件持久化
- **当** 发布领域事件
- **那么** 事件必须持久化存储，确保不丢失

#### 场景:事件重试
- **当** 事件处理失败
- **那么** 系统必须支持重试机制
