## 为什么

当前项目缺少完整的人员选择组件，现有 `people-select` 组件功能不完善，缺少 Popover 快速搜索、三态复选框、头像展示、人员详情卡片等核心功能。参考 Alon 项目成熟的人员选择组件实现，需要将其迁移至本项目，同时遵循本项目统一的树模型和响应对象规范。

## 变更内容

### 后端新增

- **新增 API**：`/iam/console/v1/org-users/tree` — 组织人员混合树查询
- **新增 API**：`/iam/console/v1/org-users/{org_id}/users` — 组织下人员查询
- **新增 API**：`/iam/console/v1/users/search` — 人员搜索（分页）
- **新增 API**：`/iam/console/v1/users/batch` — 批量获取用户
- **新增 API**：`/iam/console/v1/users/{user_id}/avatar` — 用户头像获取
- **新增 API**：`/iam/console/v1/organizations/search` — 组织搜索（分页）
- **新增 API**：`/iam/console/v1/organizations/batch` — 批量获取组织

### 后端扩展

- 扩展 `OrganizationTreeResponse`，添加 `has_org_num`、`has_user_num`、`users[]` 字段
- 扩展 `UserResponse`，添加 `org_tree_names` 字段

### 前端新增

- **PeopleSelect.vue** — 主入口组件（Popover 搜索 + Badge 展示）
- **PeopleSelectView.vue** — 选择视图（左右布局）
- **PeopleSelectDialog.vue** — 弹窗封装
- **PeopleDisplay.vue** — 人员展示（Popover 卡片）
- **PeopleAvatar.vue** — 头像组件
- **OrgTreeNode.vue** — 组织树节点（递归渲染）
- **UserTreeNode.vue** — 人员树节点
- **useOrgPeopleTree.ts** — 核心逻辑 composable（三态复选、懒加载）
- **service.ts** — API 封装（请求合并 + 缓存）
- **OrganizationSelect.vue** — 组织选择主入口
- **OrganizationSelectView.vue** — 组织选择视图
- **OrganizationSelectDialog.vue** — 组织选择弹窗

## 功能 (Capabilities)

### 新增功能

- `people-select`: 人员选择组件 — 支持 Popover 快速搜索、左右布局选择、三态复选框、头像展示、人员详情卡片
- `organization-select`: 组织选择组件 — 支持组织树选择、搜索、多选
- `org-user-tree-api`: 组织人员树 API — 提供组织人员混合树查询、懒加载、搜索能力

### 修改功能

- 无现有功能需求变更

## 影响

### 后端影响

- **新增控制器**：`src/iam/controllers/console/org_user_controller.py`
- **扩展服务**：`src/iam/services/organization_service.py`、`src/iam/services/user_service.py`
- **新增 Schema**：`src/iam/schemas/org_user.py`
- **数据库查询**：需统计组织下人员数量和子组织数量

### 前端影响

- **新增目录**：`web/vue/src/components/common/feedback/people-select/components/`
- **新增目录**：`web/vue/src/components/common/feedback/people-select/composables/`
- **新增目录**：`web/vue/src/components/common/feedback/people-select/organization/`
- **类型扩展**：`web/vue/src/components/common/feedback/people-select/types.ts`

### 兼容性考虑

- 新增 API 和组件，不影响现有功能
- 类型定义遵循本项目 `TreeNode` 体系，不引入 Alon 项目类型
- API 响应格式遵循本项目 `ApiResponse` 规范
