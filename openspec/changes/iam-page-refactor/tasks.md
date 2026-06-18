## 1. 后端 API 补充

- [x] 1.1 新增 Schema：`iam/schemas/department.py` 添加 `DepartmentUserBatchRequest`、`UserStatsResponse`、`DepartmentDetailResponse`（含 direct_member_count、total_member_count、path）
- [x] 1.2 新增 Schema：`iam/schemas/user.py` 添加 `UserPaginatedQuery` 扩展字段（dept_id、include_children）、`UserStatsResponse`
- [x] 1.3 新增 Schema：`iam/schemas/role.py` 添加 `RoleOptionResponse`、`RoleMemberAssignRequest`
- [x] 1.4 新增 Schema：`iam/schemas/menu.py` 添加菜单树相关响应模型
- [x] 1.5 扩展 `department_service.py`：添加 `batch_add_users`、`get_department_stats` 方法
- [x] 1.6 扩展 `user_service.py`：添加 `get_user_stats`、支持 `dept_id` 和 `include_children` 筛选参数
- [x] 1.7 扩展 `role_service.py`：添加 `get_role_members`、`add_role_members`、`remove_role_member`、`get_role_options` 方法
- [x] 1.8 新增端点 `POST /iam/admin/v1/departments/{id}/users/batch`：批量添加部门成员
- [x] 1.9 新增端点 `POST /iam/admin/v1/departments/{id}/users/{uid}/enable` 和 `/disable`：启用/停用部门成员
- [x] 1.10 新增端点 `GET /iam/admin/v1/users/stats`：用户统计
- [x] 1.11 扩展端点 `GET /iam/admin/v1/users`：增加 `dept_id` 和 `include_children` 查询参数
- [x] 1.12 新增端点 `GET /iam/admin/v1/roles/options`：角色选项列表
- [x] 1.13 新增端点 `GET /iam/admin/v1/roles/{id}/members`：角色成员列表
- [x] 1.14 新增端点 `POST /iam/admin/v1/roles/{id}/members` 和 `DELETE /iam/admin/v1/roles/{id}/members/{uid}`：角色成员管理
- [x] 1.15 新增端点 `GET /iam/admin/v1/roles/{id}/menus` 和 `POST /iam/admin/v1/roles/{id}/menus`：角色菜单管理

## 2. 前端类型和 API 更新

- [x] 2.1 更新 `iam/types/index.ts`：扩展 User 类型（添加 dept_id、dept_name、dept_path、role_ids 字段）
- [x] 2.2 更新 `iam/types/index.ts`：扩展 Department 类型（添加 direct_member_count、total_member_count、path 字段）
- [x] 2.3 新增 `iam/types/index.ts`：添加 `UserStats`、`RoleOption`、`OrgTreeNode`、`PeopleItem` 类型
- [x] 2.4 更新 `iam/api/department.ts`：添加批量添加成员、启用/停用成员、部门详情 API 函数
- [x] 2.5 更新 `iam/api/user.ts`：添加用户统计、按部门筛选、角色选项 API 函数
- [x] 2.6 更新 `iam/api/role.ts`：添加角色成员管理、角色菜单管理 API 函数

## 3. 通用组件：PeopleSelectDialog

- [x] 3.1 创建 `components/common/feedback/people-select/types.ts`：定义 OrgTreeNode、PeopleItem、PeopleSelectEvent 等类型
- [x] 3.2 实现 `components/common/feedback/people-select/usePeopleTree.ts`：组织+人员树的无头逻辑 composable（三态复选、懒加载、搜索）
- [x] 3.3 实现 `components/common/feedback/people-select/PeopleSelectView.vue`：选择视图（左树+右列表布局）
- [x] 3.4 实现 `components/common/feedback/people-select/PeopleSelectDialog.vue`：弹窗封装（Dialog + PeopleSelectView + 确认/取消按钮）
- [x] 3.5 创建 `components/common/feedback/people-select/index.ts`：统一导出
- [x] 3.6 更新 `components/common/feedback/index.ts` 和 `components/index.ts`：添加 PeopleSelectDialog 导出

## 4. 部门管理页面改造

- [x] 4.1 创建 `iam/components/CreateDepartmentDialog.vue`：部门创建/编辑弹窗（vee-validate+zod 表单验证、上级部门 TreeSelect、名称/编码/排序号/负责人字段）
- [x] 4.2 重写 `iam/pages/departments/DepartmentPage.vue`：左右布局 + Header + Tabs 三标签（组织信息、下级组织、直属成员）
- [x] 4.3 实现组织树搜索高亮功能
- [x] 4.4 实现骨架屏加载状态
- [x] 4.5 实现"下级组织"Tab 表格展示和"查看"跳转
- [x] 4.6 实现"直属成员"Tab（表格 + 添加成员 PeopleSelectDialog + 启用/禁用/删除操作）

## 5. 人员管理页面改造

- [x] 5.1 创建 `iam/components/UserFormDialog.vue`：用户创建/编辑弹窗（表单验证、部门 TreeSelect、角色 Checkbox 列表）
- [x] 5.2 重写 `iam/pages/users/UserList.vue`：统计卡片区 + 左侧部门树筛选 + 右侧 DataTable 人员列表
- [x] 5.3 实现多条件筛选（关键词搜索、状态下拉、角色下拉）
- [x] 5.4 实现行内操作（编辑、启用/禁用、重置密码、删除）
- [x] 5.5 重置筛选和清空部门筛选功能

## 6. 账户管理页面改造

- [x] 6.1 重写 `iam/pages/profile/Profile.vue`：头像区 + 横向 Tabs（个人信息、安全设置）
- [x] 6.2 实现个人信息表单（vee-validate+zod 验证，昵称/邮箱/手机号）
- [x] 6.3 实现修改密码弹窗（原密码/新密码/确认密码 + 显示/隐藏切换 + zod 验证）

## 7. 权限管理页面改造

- [x] 7.1 重写 `iam/pages/permissions/PermissionList.vue`：左右布局 + Tabs（角色列表、菜单列表）
- [x] 7.2 实现左侧权限树（按资源分组 + 搜索过滤）
- [x] 7.3 实现"角色列表"Tab（角色表格 + 分配权限弹窗）
- [x] 7.4 实现"菜单列表"Tab（菜单树展示）

## 8. 角色管理页面改造

- [ ] 8.1 重写 `iam/pages/roles/RoleList.vue`：左侧角色列表 + 右侧 Tabs（角色成员、权限列表）
- [ ] 8.2 实现"角色成员"Tab（成员表格 + 添加成员 PeopleSelectDialog + 移除成员）
- [ ] 8.3 实现"权限列表"Tab（按资源分组的权限展示 + 分配权限弹窗）

## 9. 测试

- [ ] 9.1 后端单元测试：新增 API 端点的请求/响应测试
- [ ] 9.2 后端单元测试：Service 层新方法测试（batch_add_users、get_user_stats 等）
- [ ] 9.3 前端组件测试：PeopleSelectDialog 组件测试（单选、多选、禁用、搜索）
- [ ] 9.4 前端页面测试：DepartmentPage 重写后的关键交互测试