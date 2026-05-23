## Why

IAM 前端模块主体功能已实现并归档，但仍有 7 项遗留任务未完成，包括：权限树组件、部门树组件、登录历史功能、Framework 集成完善（侧边栏菜单、租户上下文、权限指令）以及测试与性能优化。这些功能对于完整的管理后台体验至关重要。

## What Changes

- 创建权限树组件 `PermissionTree.vue`，支持树形权限选择和分配
- 创建部门树组件 `DepartmentTree.vue`，支持树形部门展示和选择
- 实现登录历史查看功能，展示用户登录记录
- 更新 Framework 侧边栏菜单，集成 IAM 模块菜单项
- 扩展用户状态，增加租户上下文信息（当前租户、租户列表）
- 集成权限指令 `v-permission`，支持页面内按钮级权限控制
- 创建 API 单元测试、Store 单元测试、关键页面组件测试
- 优化大数据量性能（虚拟滚动、懒加载）

## Capabilities

### New Capabilities

- `login-history`: 登录历史功能，支持查看用户登录记录、登录时间、IP 地址、设备信息
- `permission-tree`: 权限树组件，支持树形权限展示、批量选择、权限分配
- `department-tree`: 部门树组件，支持树形部门展示、节点选择、拖拽排序
- `framework-iam-integration`: Framework 与 IAM 模块集成，包括侧边栏菜单、租户上下文、权限指令
- `iam-frontend-tests`: IAM 前端测试套件，包含 API 测试、Store 测试、组件测试

### Modified Capabilities

- `authentication`: 扩展认证功能，增加登录历史记录查看
- `permission-system`: 扩展权限系统，增加 `v-permission` 指令支持
- `user-management`: 扩展用户状态，增加租户上下文信息

## Impact

### 受影响的代码

- `web/vue/src/iam/components/` - 新增权限树、部门树组件
- `web/vue/src/iam/pages/profile/Profile.vue` - 增加登录历史 Tab
- `web/vue/src/iam/api/auth.ts` - 新增获取登录历史 API
- `web/vue/src/framework/stores/user.ts` - 扩展租户上下文
- `web/vue/src/framework/components/layout/` - 更新侧边栏菜单
- `web/vue/src/framework/directives/` - 新增权限指令
- `web/vue/tests/iam/` - 新增测试文件

### 受影响的 API

| API 端点 | 功能 |
|----------|------|
| `/api/v1/auth/login-history` | 获取登录历史记录（新增） |

### 兼容性考虑

- 权限指令需兼容现有权限检查逻辑
- 侧边栏菜单需支持动态路由和权限过滤
- 租户上下文需与现有用户状态兼容
