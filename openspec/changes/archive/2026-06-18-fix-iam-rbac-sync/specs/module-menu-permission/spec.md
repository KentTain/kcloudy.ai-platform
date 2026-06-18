## 新增需求

### 需求:模块菜单权限关联模型

系统必须支持在模块定义层定义菜单所需的权限。

#### 场景:创建模块菜单权限关联
- **当** 模块管理员创建菜单权限关联，提供 module_menu_id 和 module_permission_id
- **那么** 创建 ModuleMenuPermission 记录，建立菜单与权限的关联

#### 场景:唯一性约束
- **当** 尝试创建重复的菜单权限关联
- **那么** 返回唯一性约束错误

#### 场景:级联删除
- **当** 模块菜单被删除
- **那么** 该菜单关联的所有 ModuleMenuPermission 记录自动删除

#### 场景:权限级联删除
- **当** 模块权限被删除
- **那么** 该权限关联的所有 ModuleMenuPermission 记录自动删除

### 需求:模块菜单权限同步

系统必须在租户分配模块时同步菜单权限关联到租户实例层。

#### 场景:模块分配时同步菜单权限
- **当** 租户分配模块
- **那么** 同步该模块下所有 ModuleMenuPermission 到 MenuPermission

#### 场景:同步映射规则
- **当** 同步 ModuleMenuPermission 到 MenuPermission
- **那么** 通过 ref_id 查找租户实例层的 Menu 和 Permission ID

#### 场景:新增菜单权限关联同步
- **当** 模块新增菜单权限关联（已分配模块）
- **那么** 为所有已分配该模块的租户创建 MenuPermission 记录

#### 场景:删除菜单权限关联同步
- **当** 模块删除菜单权限关联
- **那么** 删除所有租户对应的 MenuPermission 记录

### 需求:菜单权限查询

系统必须支持查询模块菜单的权限列表。

#### 场景:查询菜单权限
- **当** 模块管理员请求 `GET /tenant/admin/v1/modules/{id}/menus/{menu_id}/permissions`
- **那么** 返回该菜单关联的所有权限列表

#### 场景:更新菜单权限
- **当** 模块管理员请求 `PUT /tenant/admin/v1/modules/{id}/menus/{menu_id}/permissions`
- **那么** 更新菜单权限关联列表
