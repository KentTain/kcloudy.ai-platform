## 新增需求

### 需求:系统必须提供组织管理功能

系统必须提供组织管理功能，替代原有的部门管理功能，支持树形组织结构和负责人设置。

#### 场景:组织模型定义
- **当** 定义组织模型时
- **那么** 组织表名必须为 `organizations`
- **且** 支持树形结构（`parent_id`、`tree_level`、`tree_leaf` 等字段）
- **且** 支持设置组织负责人（`leader_id`）

#### 场景:顶级组织
- **当** 创建顶级组织时
- **那么** `parent_id` 可以为 `NULL`
- **且** 组织可以有子组织

### 需求:组织管理 API 必须使用新路径

组织管理 API 必须使用 `/iam/admin/v1/organizations` 路径，替代原有的 `/iam/admin/v1/departments`。

#### 场景:组织列表查询
- **当** 管理员请求 `GET /iam/admin/v1/organizations` 时
- **那么** 系统必须返回组织列表
- **且** 支持树形结构展示

#### 场景:组织创建
- **当** 管理员请求 `POST /iam/admin/v1/organizations` 时
- **那么** 系统必须创建组织记录
- **且** 自动维护树形结构字段（`tree_level`、`tree_leaf`、`parent_ids` 等）

#### 场景:组织更新
- **当** 管理员请求 `PUT /iam/admin/v1/organizations/{id}` 时
- **那么** 系统必须更新组织信息
- **且** 如果修改了 `parent_id`，必须重新计算所有子组织的树形字段

#### 场景:组织删除
- **当** 管理员请求 `DELETE /iam/admin/v1/organizations/{id}` 时
- **那么** 系统必须检查是否存在子组织
- **且** 如果存在子组织，必须拒绝删除并返回错误

### 需求:用户-组织关联必须支持负责人标识

用户与组织的关联（`user_organizations` 表）必须支持标识用户是否为该组织的负责人。

#### 场景:用户加入组织
- **当** 将用户添加到组织时
- **那么** 系统必须创建 `user_organizations` 记录
- **且** 可以设置 `is_leader = true` 标识用户为组织负责人

#### 场景:组织负责人设置
- **当** 设置组织负责人时
- **那么** 系统必须同时更新 `organizations.leader_id` 和 `user_organizations.is_leader`
- **且** 确保数据一致性

### 需求:菜单名称必须更新

IAM 模块的菜单"部门管理"必须重命名为"组织管理"。

#### 场景:菜单显示
- **当** 用户查看 IAM 模块菜单时
- **那么** 菜单名称必须显示为"组织管理"
- **且** 菜单编码必须为 `iam.organizations`
- **且** 路由路径必须为 `/iam/organizations`

### 需求:权限编码必须更新

组织管理相关的权限编码必须从 `iam:department:*` 更新为 `iam:organization:*`。

#### 场景:权限编码变更
- **当** 定义组织管理权限时
- **那么** 权限编码格式必须为 `iam:organization:read`、`iam:organization:write`、`iam:organization:delete`
- **且** 资源名称必须为 `organization`

### 需求:前端页面必须更新

前端必须更新所有部门相关的页面、组件、API 和类型定义。

#### 场景:前端路由更新
- **当** 用户访问组织管理页面时
- **那么** 路由路径必须为 `/iam/organizations`
- **且** 页面组件必须为 `OrganizationPage.vue`

#### 场景:前端类型更新
- **当** 定义组织类型时
- **那么** TypeScript 接口名必须为 `Organization`
- **且** 字段定义与后端模型一致
