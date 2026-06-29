## 1. 后端 Schema 定义

- [x] 1.1 创建 `src/iam/schemas/org_user.py`，定义 `UserSimpleVo`（用户简要信息）
- [x] 1.2 创建 `OrgUserTreeVo`（组织人员树节点），继承 `TreeNodeTreeVo`
- [x] 1.3 创建 `OrganizationSimpleVo`（组织简要信息），继承 `TreeNodeVo`
- [x] 1.4 创建请求/响应模型：`UserSearchQuery`、`OrgUsersQuery`、`UserBatchBody` 等

## 2. 后端 Service 层扩展

- [x] 2.1 扩展 `src/iam/services/organization_service.py`，添加 `get_org_user_tree()` 方法
- [x] 2.2 添加 `get_org_users()` 方法，支持递归查询组织下人员
- [x] 2.3 添加 `search_organizations()` 方法，支持分页搜索组织
- [x] 2.4 添加 `get_organizations_by_ids()` 方法，支持批量获取组织
- [x] 2.5 扩展 `src/iam/services/user_service.py`，添加 `search_users()` 方法
- [x] 2.6 添加 `get_users_by_ids()` 方法，支持批量获取用户
- [x] 2.7 添加 `get_user_avatar_url()` 方法，返回用户头像 URL

## 3. 后端 Controller 层

- [x] 3.1 创建 `src/iam/controllers/console/org_user_controller.py`
- [x] 3.2 实现 `GET /iam/console/v1/org-users/tree` 端点
- [x] 3.3 实现 `GET /iam/console/v1/org-users/{org_id}/users` 端点
- [x] 3.4 实现 `GET /iam/console/v1/users/search` 端点
- [x] 3.5 实现 `POST /iam/console/v1/users/batch` 端点
- [x] 3.6 实现 `GET /iam/console/v1/users/{user_id}/avatar` 端点
- [x] 3.7 实现 `GET /iam/console/v1/organizations/search` 端点
- [x] 3.8 实现 `POST /iam/console/v1/organizations/batch` 端点
- [x] 3.9 在 `src/iam/controllers/console/__init__.py` 中注册路由

## 4. 前端类型定义

- [x] 4.1 创建 `web/vue/src/components/common/feedback/people-select/types.ts`
- [x] 4.2 定义 `UserItem`、`OrgTreeNode`、`OrganizationItem` 接口
- [x] 4.3 定义 `UserModelValue`、`UserItemValue`、`OrganizationModelValue` 类型
- [x] 4.4 定义 `UserConfirmEvent`、`OrganizationConfirmEvent` 事件类型
- [x] 4.5 定义 `CheckState`、`SelectTarget`、`FlatNode` 类型

## 5. 前端 API 封装

- [x] 5.1 创建 `web/vue/src/components/common/feedback/people-select/service.ts`
- [x] 5.2 实现 `fetchUserDetails()` 函数（请求合并 + 缓存）
- [x] 5.3 实现 `fetchOrganizationDetails()` 函数（请求合并 + 缓存）
- [x] 5.4 实现 `searchUsers()` 函数（分页搜索）
- [x] 5.5 实现 `searchOrganizations()` 函数（分页搜索）
- [x] 5.6 实现 `loadOrgUserTree()` 函数（加载组织人员树）

## 6. 前端 Composable

- [x] 6.1 创建 `web/vue/src/framework/composables/useTreeExpand.ts`（公共：树展开/折叠）
- [x] 6.2 创建 `web/vue/src/framework/composables/useTreeCheck.ts`（公共：三态复选框）
- [x] 6.3 创建 `web/vue/src/components/common/feedback/people-select/useOrgPeopleTree.ts`
- [x] 6.4 实现扁平化节点计算 `flatVisibleNodes`
- [x] 6.5 实现懒加载逻辑 `toggleExpand()`、`loadRoot()`
- [x] 6.6 实现选择逻辑 `toggleUserCheck()`、`toggleOrgCheck()`

## 7. 前端基础组件（people-select）

- [x] 7.1 创建 `web/vue/src/components/common/feedback/people-select/PeopleAvatar.vue`
- [x] 7.2 创建 `web/vue/src/components/common/feedback/people-select/OrgTreeNode.vue`
- [x] 7.3 创建 `web/vue/src/components/common/feedback/people-select/UserTreeNode.vue`

## 8. 前端视图组件（people-select）

- [x] 8.1 创建 `web/vue/src/components/common/feedback/people-select/PeopleSelectView.vue`
- [x] 8.2 创建 `web/vue/src/components/common/feedback/people-select/PeopleSelectDialog.vue`
- [x] 8.3 创建 `web/vue/src/components/common/feedback/people-select/PeopleSelect.vue`
- [x] 8.4 创建 `web/vue/src/components/common/feedback/people-select/PeopleDisplay.vue`
- [x] 8.5 更新 `web/vue/src/components/common/feedback/people-select/index.ts`

## 9. 组织选择器组件（org-select）

- [x] 9.1 创建 `web/vue/src/components/common/feedback/org-select/types.ts`
- [x] 9.2 创建 `web/vue/src/components/common/feedback/org-select/useOrgTree.ts`
- [x] 9.3 创建 `web/vue/src/components/common/feedback/org-select/OrgTreeNode.vue`
- [x] 9.4 创建 `web/vue/src/components/common/feedback/org-select/OrganizationSelectView.vue`
- [x] 9.5 创建 `web/vue/src/components/common/feedback/org-select/OrganizationSelectDialog.vue`
- [x] 9.6 创建 `web/vue/src/components/common/feedback/org-select/OrganizationSelect.vue`
- [x] 9.7 创建 `web/vue/src/components/common/feedback/org-select/index.ts`

## 10. 组件导出与文档

- [x] 10.1 更新 `web/vue/src/components/common/feedback/index.ts` 导出
- [x] 10.2 更新 `web/vue/src/components/index.ts` 统一入口
- [x] 10.3 更新 `web/vue/src/components/common/CLAUDE.md` 文档

## 11. 后端测试

- [x] 11.1 创建 `tests/iam/unit/test_org_user_service.py`
- [x] 11.2 测试 `get_org_user_tree()` 方法
- [x] 11.3 测试 `search_users()` 方法
- [x] 11.4 测试 `get_users_by_ids()` 方法
- [x] 11.5 创建 `tests/iam/unit/test_org_user_controller.py`
- [x] 11.6 测试各 API 端点

## 12. 前端测试

- [x] 12.1 创建 `tests/components/unit/people-select/` 目录
- [x] 12.2 创建 `useOrgPeopleTree.test.ts`
- [x] 12.3 测试三态复选框逻辑
- [x] 12.4 测试懒加载逻辑
- [x] 12.5 测试选择逻辑
- [x] 12.6 创建 `PeopleSelect.test.ts`
- [x] 12.7 测试组件渲染和交互
