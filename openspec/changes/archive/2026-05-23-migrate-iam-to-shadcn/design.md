## Context

IAM 模块 11 个页面和 2 个树组件全部使用 Element Plus（23 种 el-xxx 组件），与项目已完成的 shadcn-vue + Tailwind CSS 方向不一致。AdminLayout 已迁移至 shadcn Sidebar，IAM 页面仍停留在 Element Plus 视觉风格。vee-validate + zod 已安装但 IAM 表单仍用 el-form rules。

本次迁移涉及 13 个文件的重写，是项目中最大的单次 UI 变更。关键策略是逐页面迁移，每个页面独立可测试。

## Goals / Non-Goals

**Goals:**
- IAM 模块全部页面和组件从 Element Plus → shadcn 组件体系
- 表单校验从 el-form rules → vee-validate + zod schema
- 列表页从 el-table + el-pagination → shadcn Table + 自写 Pagination
- 树组件从 el-tree → 自写 CheckboxTree
- 详情页从 el-descriptions → 自写 DescriptionList
- v-loading → Skeleton 加载态
- el-tag → Badge
- el-tabs → shadcn Tabs（需安装）
- el-dialog → shadcn Dialog（已安装）
- el-date-picker → 自写 DatePicker 或第三方（date-fns）
- 先 UserList 验证 Table + Pagination 组合可行，再批量迁移

**Non-Goals:**
- 不改变 Store/API 层逻辑
- 不改变路由配置
- 不引入新业务功能
- 不全局移除 Element Plus 注册（其他模块可能仍在使用）
- 不重构 IAM 模块目录结构

## Decisions

### D1: Pagination — 自写 vs 第三方 vs shadcn-vue 官方

**选择：自写 IamPagination 组件**

shadcn-vue 无官方 Pagination 组件。自写组件基于 Tailwind CSS 样式，支持页码跳转、每页条数切换、总数显示。放在 `web/vue/src/components/` 供全局复用。

替代方案：使用 AlonDataTablePagination（kbhub 项目）— 可借鉴但直接引入会增加跨项目依赖。

### D2: Tree — 自写 CheckboxTree vs shadcn-vue 官方

**选择：自写 CheckboxTree 组件**

shadcn-vue 无 Tree 组件。自写递归树组件支持勾选/半选（indeterminate）、搜索过滤、展开折叠。PermissionTree 和 DepartmentTree 作为 CheckboxTree 的业务封装层。

替代方案：引入 vue3-tree-view 等第三方库 — 增加 npm 依赖且风格不一致。

### D3: DescriptionList — 自写 vs shadcn 封装

**选择：自写 DescriptionList 组件**

el-descriptions 的 key-value 展示是常见模式，shadcn 无对应组件。自写组件用 grid 布局实现 label + value 对齐展示。放在 `web/vue/src/components/`。

### D4: Tabs — 安装 shadcn Tabs

**选择：`npx shadcn-vue@latest add tabs`**

PermissionList 和 Profile 使用 el-tabs，shadcn-vue 有官方 Tabs 组件，直接安装使用。

### D5: DatePicker — 自写 vs 第三方

**选择：date-fns + 自写 DateInput 组件**

TenantForm（datetime）和 Profile（daterange）使用 el-date-picker，这是最复杂的迁移点。选择 date-fns 作为日期工具库 + 自写 DateInput（单日期 + 日期范围），基于 shadcn Input + Popover 模式。

替代方案：引入 vue-datepicker 或 v-calendar — 增加 npm 依赖且与 shadcn 视觉风格不一致。

### D6: 表单校验迁移策略

**选择：vee-validate + zod schema 逐表单替换**

每个表单页面独立定义 zod schema，使用 shadcn FormField/FormItem/FormLabel/FormMessage。el-form rules 的 required/min/max 等规则映射为 zod 的 string().min().max()。

### D7: 加载态迁移策略

**选择：Skeleton 行级占位替代 v-loading**

shadcn-vue 无 loading directive。列表页用 Skeleton TableRow 占位，详情页用 Skeleton 行占位，保持视觉一致性。

### D8: 迁移顺序

**选择：UserList → RoleList → TenantList → DepartmentPage → UserForm/RoleForm/TenantForm → UserDetail/TenantDetail → PermissionList → Profile → PermissionTree/DepartmentTree**

先做列表页验证 Table + Pagination 组合，再做表单页验证 vee-validate，再做详情页验证 DescriptionList，最后做树组件和最复杂的 Profile（4 tabs）。

## Risks / Trade-offs

- [自写组件质量] → CheckboxTree/DescriptionList/DateInput/Pagination 均为自写，需要充分测试覆盖。先 UserList 验证基础模式可行再批量推进
- [Profile 页复杂度] → Profile 有 4 tabs + 2 tables + 2 date-pickers + 多个表单，是最复杂页面。作为最后迁移，前面的经验可复用
- [el-date-picker 替换] → datetime 和 daterange 模式复杂，自写 DateInput 可能功能不如 Element Plus 完善。先简化为基本可用，后续迭代增强
- [Element Plus 全局注册保留] → IAM 不再使用但其他模块可能仍依赖，全局注册暂不移除
- [视觉一致性] → 自写组件需严格遵循 shadcn 设计令牌（bg-background, text-foreground 等），确保与 shadcn 原生组件视觉一致