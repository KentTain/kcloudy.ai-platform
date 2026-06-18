## 修改需求

### 需求:用户类型扩展
前端 User 类型必须扩展以支持人员管理页面和人员选择器所需字段。

#### 场景:新增字段
- **当** 后端返回用户数据包含 `dept_id`、`dept_name`、`dept_path`、`role_ids`、`status`(enum) 字段
- **那么** 前端 User 类型必须包含这些字段，用于人员列表展示和筛选

### 需求:部门类型扩展
前端 Department 类型必须扩展以支持组织树展示。

#### 场景:新增字段
- **当** 后端返回部门数据包含 `direct_member_count`、`total_member_count`、`path` 字段
- **那么** 前端 Department 类型必须包含这些字段，用于组织详情统计信息展示

### 需求:新增角色选项类型
前端必须新增 RoleOption 类型用于下拉选择。

#### 场景:角色选项下拉
- **当** 调用角色选项 API
- **那么** 返回 RoleOption 类型包含 `id`、`name`、`code`、`description` 字段

### 需求:新增用户统计类型
前端必须新增 UserStats 类型。

#### 场景:用户统计数据
- **当** 调用用户统计 API
- **那么** 返回 UserStats 类型包含 `total`、`enabled`、`disabled`、`multi_role` 四个数字字段