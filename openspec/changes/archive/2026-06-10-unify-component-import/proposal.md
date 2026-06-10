## 为什么

当前业务模块（tenant/iam/demo 等）开发页面时直接使用 `@/components/ui/` 原始组件，而 `@/components/common/` 提供的业务封装版本（如 Button +loading/block、Input +clearable/error）未被使用。原因是缺少统一导入入口，开发者默认选择了"看起来更底层"的 ui 组件，导致业务封装价值未被利用，页面代码冗余。

## 变更内容

### 新增

- 创建 `web/vue/src/components/index.ts` 统一组件入口
- 统一入口导出策略：
  - **同名组件**：common 优先（Button, Input, Card, Select, Table 覆盖 ui 版本）
  - **高频 ui 组件**：重导出 Badge, Skeleton, Dialog, Tabs, Form, Checkbox, Switch, Textarea, Label
  - **低频 ui 组件**：仍从 `@/components/ui/xxx` 单独导入
- 类型导出：TreeSelectProps, DescriptionItem, DataTableState, MessageBoxOptions 等

### 迁移

将业务模块的组件导入统一迁移到 `@/components` 入口：

| 模块 | 文件数 | 范围 |
|------|--------|------|
| tenant | 12 | pages, components, layouts |
| iam | 11 | pages, components |
| demo | 4 | pages |
| framework | 12 | pages, layouts, components |
| ai | 3 | pages, components |

**BREAKING** 无破坏性变更 —— 原 `@/components/ui/xxx` 和 `@/components/common` 导入路径仍可用，统一入口为新增能力。

## 功能 (Capabilities)

### 新增功能

- `unified-component-import`: 统一组件导入入口规范，定义组件查找优先级和导出规则

### 修改功能

无 —— 此变更为新增基础设施，不影响现有功能的行为规范。

## 影响

### 代码影响

- **新增文件**：`web/vue/src/components/index.ts`
- **修改文件**：42 个业务模块 Vue 文件的 import 语句
- **不修改**：`common/` 和 `ui/` 目录下的组件实现

### 组件映射关系

| 组件 | 原导入路径 | 新导入路径 | 实际来源 |
|------|-----------|-----------|---------|
| Button | `@/components/ui/button` | `@/components` | common (覆盖 ui) |
| Input | `@/components/ui/input` | `@/components` | common (覆盖 ui) |
| Card | `@/components/ui/card` | `@/components` | common (覆盖 ui) |
| Select | `@/components/ui/select` | `@/components` | common (声明式) |
| Table | `@/components/ui/table` | `@/components` | common (声明式) |
| Badge | `@/components/ui/badge` | `@/components` | ui (重导出) |
| Dialog | `@/components/ui/dialog` | `@/components` | ui (重导出) |
| Tree | `@/components/ui/tree` | 保持原路径 | ui (与 common/Tree 不兼容) |

### 文档影响

- 更新 `web/vue/src/CLAUDE.md`：组件复用查找优先级章节
- 更新 `web/vue/src/components/common/CLAUDE.md`：导入方式章节
- 新增 memory：`component-import-priority.md`

### 依赖影响

无新增外部依赖，纯内部重构。
