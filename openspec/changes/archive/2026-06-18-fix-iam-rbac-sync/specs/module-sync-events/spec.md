## 新增需求

### 需求:模块菜单权限变更事件

系统必须在模块菜单权限关联变更时发布事件。

#### 场景:发布 ModuleMenuPermissionCreated 事件
- **当** 模块新增菜单权限关联
- **那么** 发布 ModuleMenuPermissionCreated 事件，携带 module_menu_permission_id

#### 场景:发布 ModuleMenuPermissionDeleted 事件
- **当** 模块删除菜单权限关联
- **那么** 发布 ModuleMenuPermissionDeleted 事件，携带 module_menu_id 和 module_permission_id

## 修改需求

### 需求:模块角色权限变更事件

系统必须在模块角色权限关联变更时发布详细事件。

#### 场景:发布 ModuleRolePermissionCreated 事件
- **当** 模块角色新增权限关联
- **那么** 发布 ModuleRolePermissionCreated 事件，携带 module_role_permission_id

#### 场景:发布 ModuleRolePermissionDeleted 事件
- **当** 模块角色删除权限关联
- **那么** 发布 ModuleRolePermissionDeleted 事件，携带 module_role_id 和 module_permission_id
