## 上下文

IAM 模块当前有 5 个管理页面（部门、人员、账户、权限、角色），功能简陋：平铺表格无组织树交互、无 Tabs 详情面板、无人员选择器。参照 kbhub 项目成熟交互模式进行全面改造。改造涉及前后端全栈：后端需补全 API 接口，前端需重写 5 个页面 + 新增 3 个组件。

当前技术栈：
- 后端：FastAPI + SQLAlchemy 2.0 + Pydantic 2.x，三层架构（Controller → Service → Model）
- 前端：Vue 3 + TypeScript + Pinia + shadcn-vue + Tailwind CSS v4 + vee-validate + zod

关键约束：
- 公共组件放 `src/components/common/`，模块专用组件放 `src/iam/components/`
- API 路由遵循 `/{模块}/{类型}/v1/{功能}` 格式
- 后端 Service 是主要业务逻辑入口，Controller 只处理路由和参数校验

## 目标 / 非目标

**目标：**
- 部门管理：左右布局 + Tabs（组织信息、下级组织、直属成员），支持搜索高亮、骨架屏、创建/编辑弹窗、人员选择器添加成员
- 人员管理：统计卡片 + 左侧部门树筛选 + 右侧 DataTable，支持多条件筛选、行内操作、角色分配
- 账户管理：头像区 + Tabs（个人信息表单、安全设置含密码修改弹窗）
- 权限管理：左右布局 + Tabs（角色列表带权限分配、菜单列表带菜单分配）
- 角色管理：左列表 + 右侧 Tabs（角色成员、权限列表），支持成员选择器和权限分配
- 人员选择器：完整的组织树+人员选择弹窗（三态复选、懒加载、搜索）
- 后端 API：补全缺失的批量操作、筛选、统计、成员管理等接口

**非目标：**
- 不实现 kbhub 的国际化（i18n）功能
- 不重构后端数据模型结构（仅在现有模型上扩展接口）
- 不引入新的外部依赖（前端使用已有 vee-validate+zod，后端使用已有库）
- 不涉及租户管理模块的改动

## 决策

### D1: 页面布局采用固定左树+弹性右面板模式

**决策：** 所有具有树形选择的页面统一采用 `左侧 300px 固定宽度 + 右侧自适应填充` 布局，参照 kbhub organization.vue。

**理由：** 与当前项目 12 列栅格布局（4:8）相比，固定 300px 提供更稳定的树面板体验，右侧可用空间更多。

**替代方案：** 继续使用栅格布局（12 列 4:8），但大屏下树面板过窄，小屏下比例失调。

### D2: 人员选择器放在 common/ 组件库

**决策：** PeopleSelectDialog 放在 `src/components/common/feedback/` 目录，作为跨模块通用组件。

**理由：** 人员选择器是 IAM 核心交互，未来可能被 AI 模块（对话参与者选择）等复用。将其放在 common 与项目组件分层策略一致。

**替代方案：** 放在 `src/iam/components/`，仅 IAM 模块使用。但限制了复用性。

### D3: 人员选择器基于项目现有 Tree 组件封装

**决策：** 使用项目 `common/Tree` 组件作为底层树渲染，在其上封装 `usePeopleTree` composable 实现三态逻辑、搜索、懒加载。

**理由：** 项目已有 `common/Tree` 组件（支持 checkbox、cascade、loadData），与 shadcn-ui 风格一致。kbhub 的 AlonPeopleSelect 使用的是 shadcn-tree，两者设计理念相近。基于现有组件封装减少新依赖。

**替代方案：** 直接移植 kbhub 的 ShadcnTree + useOrgPeopleTree。但需适配两套树组件的 API 差异，且增加了维护成本。

### D4: DataTable 替代 AlonDataTable

**决策：** 使用项目已有的 `common/DataTable` 组件（基于 @tanstack/vue-table），不用 kbhub 的 AlonDataTable。

**理由：** 项目已有封装完善的 DataTable + DataTablePagination + useDataTable，功能等价于 kbhub 的 AlonDataTable。复用已有组件保持一致性。

### D5: 表单验证统一使用 vee-validate + zod

**决策：** 所有表单验证采用 vee-validate + zod 方案，与 kbhub 一致。

**理由：** 项目已在 Profile.vue 等页面使用 vee-validate + zod，保持统一。zod schema 可前后端共享验证逻辑。

### D6: 后端 API 补充策略

**决策：** 在现有 Controller 和 Service 上扩展新端点，不修改已有端点的响应格式。新增端点遵循已有命名规范。

**新增端点：**

| 端点 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 批量添加部门成员 | POST | `/iam/admin/v1/departments/{id}/users/batch` | 批量添加成员到部门 |
| 启用部门成员 | POST | `/iam/admin/v1/departments/{id}/users/{uid}/enable` | 启用成员 |
| 停用部门成员 | POST | `/iam/admin/v1/departments/{uid}/users/{uid}/disable` | 停用成员 |
| 用户统计 | GET | `/iam/admin/v1/users/stats` | 返回总数、启用、停用、多角色统计 |
| 角色选项列表 | GET | `/iam/admin/v1/roles/options` | 角色下拉选项（不分页） |
| 角色成员列表 | GET | `/iam/admin/v1/roles/{id}/members` | 角色下的用户列表 |
| 分配角色成员 | POST | `/iam/admin/v1/roles/{id}/members` | 为角色分配成员 |
| 移除角色成员 | DELETE | `/iam/admin/v1/roles/{id}/members/{uid}` | 移除角色成员 |
| 角色菜单列表 | GET | `/iam/admin/v1/roles/{id}/menus` | 角色已分配的菜单 |
| 分配角色菜单 | POST | `/iam/admin/v1/roles/{id}/menus` | 为角色分配菜单 |
| 按部门筛选用户 | 扩展 | `GET /iam/admin/v1/users` | 新增 dept_id、include_children 参数 |

**理由：** RESTful 风格，遵循项目已有 `/{模块}/{类型}/v1/{功能}` 路由规范。

### D7: 状态管理策略

**决策：** 页面级状态使用组件内 `reactive`/`ref` 管理，跨页面共享状态保留 Pinia Store。复杂交互逻辑抽取为 composable。

**理由：** kbhub 模式已验证：页面独立状态放组件内更简洁，不需要为每个页面都建 Store。仅 auth、user 全局状态保留在 Store。PeopleSelectDialog 的树逻辑抽取为 `usePeopleTree` composable。

### D8: 反馈机制统一使用 toast + MessageBox

**决策：** 操作成功使用 `toast.success`，操作失败使用 `toast.error`，确认操作使用项目已有的 `MessageBox.confirm`。

**理由：** 项目已有 `@/framework/utils/feedback` 封装了 `notifySuccess`、`notifyError`、`confirmAction`，与 kbhub 使用 vue-sonner + 自定义 MessageBox 模式等价。复用已有机制。

## 风险 / 权衡

- **[风险] 人员选择器复杂度高** → 三态逻辑、懒加载、搜索是核心难点。缓解：基于现有 Tree 组件的 checkbox+cascade+loadData 能力，在其上封装 usePeopleTree composable 逐步实现。
- **[风险] 后端 API 变更可能影响现有页面** → 新增端点不修改已有响应格式。新增查询参数使用可选参数，不破坏现有调用。
- **[权衡] 人员选择器放在 common vs iam** → 放在 common 增加了组件目录的复杂度，但提升了复用性。已选择 common。
- **[风险] 5 个页面同时改造工作量大** → 按阶段执行：后端 API → 部门管理 → 人员管理 → 账户管理 → 权限管理 → 角色管理。每个阶段可独立交付。
- **[风险] DataTable 不支持某些 kbhub AlonDataTable 特性** → AlonDataTable 主要是分页+远程数据获取的封装。项目 useDataTable 已覆盖这些功能，需确认是否需要补充远程数据获取的便捷方法。