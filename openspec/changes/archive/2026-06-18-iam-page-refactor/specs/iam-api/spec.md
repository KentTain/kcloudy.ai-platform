## 新增需求

### 需求:部门批量操作 API
后端必须提供部门批量成员操作接口。

#### 场景:批量添加成员
- **当** 调用 `POST /iam/admin/v1/departments/{id}/users/batch` 传入 `user_ids` 列表
- **那么** 将多个用户添加到指定部门，返回成功添加的数量

#### 场景:启用部门成员
- **当** 调用 `POST /iam/admin/v1/departments/{id}/users/{uid}/enable`
- **那么** 启用该用户账号状态

#### 场景:停用部门成员
- **当** 调用 `POST /iam/admin/v1/departments/{id}/users/{uid}/disable`
- **那么** 停用该用户账号状态

### 需求:用户统计 API
后端必须提供用户统计接口。

#### 场景:获取用户统计
- **当** 调用 `GET /iam/admin/v1/users/stats`
- **那么** 返回包含 `total`、`enabled`、`disabled`、`multi_role` 四个统计数字

### 需求:按部门筛选用户 API
后端必须支持按部门筛选用户列表。

#### 场景:筛选指定部门用户
- **当** 调用 `GET /iam/admin/v1/users?dept_id=xxx`
- **那么** 返回该部门的直属用户

#### 场景:筛选包含下级部门用户
- **当** 调用 `GET /iam/admin/v1/users?dept_id=xxx&include_children=true`
- **那么** 返回该部门及其所有下级部门的用户

### 需求:角色选项 API
后端必须提供角色选项列表接口（不分页）。

#### 场景:获取角色选项
- **当** 调用 `GET /iam/admin/v1/roles/options`
- **那么** 返回所有角色的 id、name、code、description 列表

### 需求:角色成员管理 API
后端必须提供角色成员管理接口。

#### 场景:获取角色成员
- **当** 调用 `GET /iam/admin/v1/roles/{id}/members`
- **那么** 返回该角色下的用户列表

#### 场景:分配角色成员
- **当** 调用 `POST /iam/admin/v1/roles/{id}/members` 传入 `user_ids` 列表
- **那么** 为这些用户分配该角色（追加，不覆盖已有角色）

#### 场景:移除角色成员
- **当** 调用 `DELETE /iam/admin/v1/roles/{id}/members/{uid}`
- **那么** 移除该用户的此角色

### 需求:角色菜单分配 API
后端必须提供角色菜单管理接口。

#### 场景:获取角色菜单
- **当** 调用 `GET /iam/admin/v1/roles/{id}/menus`
- **那么** 返回该角色已分配的菜单 ID 列表

#### 场景:分配角色菜单
- **当** 调用 `POST /iam/admin/v1/roles/{id}/menus` 传入 `menu_ids` 列表
- **那么** 更新该角色的菜单分配（覆盖式）