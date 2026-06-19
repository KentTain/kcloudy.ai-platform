## 上下文

IAM 模块包含 5 个使用表格展示数据的页面，当前使用 `@/components/ui/table`（手动组装）或 `@/components` Table（封装版）。需要迁移到统一的 DataTable 组件。

### 现状分析

| 页面 | 当前组件 | Table 数量 | 复杂度 |
|------|----------|------------|--------|
| UserList | 封装版 Table | 1 | 中等（分页、筛选） |
| RoleList | 手动组装 Table | 1 | 中等（Tab 内嵌） |
| PermissionList | 手动组装 Table | 1 | 简单 |
| DepartmentPage | 手动组装 Table | 2 | 较高（双表格） |
| Profile | 手动组装 Table | 1 | 简单（日期筛选） |

## 目标 / 非目标

**目标：**
- 统一使用 DataTable 组件替换所有 Table
- 保持现有 API 调用和数据结构不变
- 统一表格交互体验（分页、加载状态、空状态）
- 减少模板代码量

**非目标：**
- 不修改后端 API
- 不改变页面布局结构
- 不添加新功能

## 决策

### 1. 迁移模式选择

**决策：使用 `useDataTable` composable + `ColumnDef` 定义**

理由：
- DataTable 已封装 `useDataTable`，提供远程数据获取、分页、加载状态
- `ColumnDef` 支持类型安全，操作列使用 `h()` 函数渲染
- 参考已迁移的 `TenantList.vue` 模式

替代方案：
- ❌ 继续使用手动组装：无法获得 DataTable 的内置功能
- ❌ 封装新的 Table 变体：增加维护成本

### 2. 列定义模式

**决策：使用 `accessorKey` + `h()` 渲染函数**

```typescript
const columns: ColumnDef<User>[] = [
  {
    accessorKey: "username",
    header: "用户名",
    size: 120,
    cell: ({ row }) => h("span", { class: "font-medium" }, row.original.username),
  },
  {
    id: "actions",
    header: "操作",
    size: 200,
    cell: ({ row }) => h("div", { class: "flex items-center gap-1" }, [
      h(Button, { variant: "ghost", size: "sm", onClick: () => handleEdit(row.original) }, () => "编辑"),
    ]),
  },
]
```

理由：
- 类型安全，支持泛型
- 操作列灵活可控
- 与现有 Button/Badge 等组件无缝集成

### 3. 分页处理

**决策：使用 DataTable 内置分页**

- DataTable 内置 `DataTablePagination` 组件
- 分页状态由 `useDataTable` 自动管理
- 移除现有的独立 `Pagination` 组件

### 4. 迁移顺序

**决策：从简单到复杂**

```
Profile.vue → PermissionList.vue → RoleList.vue → UserList.vue → DepartmentPage.vue
```

理由：
- 简单页面作为练手，熟悉迁移模式
- 复杂页面在积累经验后处理

## 风险 / 权衡

### 风险 1：样式差异

- **风险**：DataTable 有默认样式，可能与现有页面风格不一致
- **缓解**：迁移后逐一验证样式，必要时调整 CSS

### 风险 2：操作按钮行为

- **风险**：`h()` 渲染的按钮事件绑定方式与模板不同
- **缓解**：参考 `TenantList.vue` 已有模式，确保事件正确绑定

### 风险 3：嵌套布局

- **风险**：部分表格在 Tabs 组件内，高度计算可能出错
- **缓解**：测试各 Tab 切换时的表格展示

### 权衡

- **代码量减少** vs **学习成本**：需要学习 `ColumnDef` 和 `h()` 函数
- **统一性** vs **灵活性**：DataTable 提供统一体验，但自定义能力略受限
