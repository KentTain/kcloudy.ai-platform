# Common 通用组件库

基于 shadcn-vue 封装的通用业务组件，按功能分类组织。

## 组件清单

### 通用组件（general/）

| 组件 | 文件 | 用途 | 主要 Props |
|------|------|------|------------|
| Button | `general/button/Button.vue` | 业务按钮 | `variant`, `size`, `loading`, `block` |
| Card | `general/card/Card.vue` | 业务卡片 | `title`, `shadow`, `padding` |

### 表单组件（form/）

| 组件 | 文件 | 用途 | 主要 Props |
|------|------|------|------------|
| Input | `form/input/Input.vue` | 业务输入框 | `modelValue`, `type`, `clearable`, `error`, `size` |
| Select | `form/select/Select.vue` | 业务选择器 | `modelValue`, `options`, `clearable`, `placeholder` |
| DateInput | `form/date-input/DateInput.vue` | 日期输入 | `modelValue`, `type`, `format`, `placeholder` |
| TreeSelect | `form/tree-select/TreeSelect.vue` | 树选择器 | `modelValue`, `data`, `multiple`, `searchable`, `cascade` |

### 数据展示组件（data-display/）

| 组件 | 文件 | 用途 | 主要 Props |
|------|------|------|------------|
| Table | `data-display/table/Table.vue` | 业务表格 | `columns`, `data`, `loading`, `stripe`, `border` |
| DataTable | `data-display/table/DataTable.vue` | 高级表格（@tanstack/vue-table） | `dataTable`, `fixedLayout` |
| DataTablePagination | `data-display/table/DataTablePagination.vue` | 表格分页 | `table` |
| Tree | `data-display/tree/Tree.vue` | 树形展示（支持 checkbox/cascade/loadData） | `data`, `checkable`, `cascade`, `modelValue`, `loadData`, `showLine`, `disabled` |
| TreeList | `data-display/tree/TreeList.vue` | 树形列表（带操作按钮） | `data`, `actions`, `defaultExpandLevel` |
| CheckboxTree | `data-display/tree/CheckboxTree.vue` | 复选框树（基于 useTreeData） | `data`, `modelValue`, `searchable`, `disabled` |
| DescriptionList | `data-display/description-list/DescriptionList.vue` | 描述列表 | `items`, `columns`, `bordered` |

### 反馈组件（feedback/）

| 组件 | 文件 | 用途 | 主要 Props |
|------|------|------|------------|
| Loading | `feedback/loading/Loading.vue` | 加载状态 | `size`, `text`, `fullscreen` |
| Modal | `feedback/modal/Modal.vue` | 业务弹窗 | `modelValue`, `title`, `size`, `closable`, `maskClosable` |
| MessageBox | `feedback/message-box/MessageBox.vue` | 消息框（服务式 API） | `title`, `content`, `type`, `showCancel` |
| SmartTooltip | `feedback/tooltip/SmartTooltip.vue` | 智能溢出提示 | `content`, `contentClass`, `onlyEllipsisOpen` |
| PeopleSelect | `feedback/people-select/PeopleSelect.vue` | 人员选择组件 | `modelValue`, `multiple`, `disabledIds` |
| OrganizationSelect | `feedback/org-select/OrganizationSelect.vue` | 组织选择组件 | `modelValue`, `multiple`, `disabledIds` |

### 导航组件（navigation/）

| 组件 | 文件 | 用途 | 主要 Props |
|------|------|------|------------|
| Pagination | `navigation/pagination/Pagination.vue` | 分页组件 | `total`, `page`, `pageSize`, `pageSizeOptions` |

## 导入方式

### 推荐：从统一入口导入

```typescript
// 统一入口 @/components 是推荐导入路径
import {
  Button, Card,
  Input, Select, DateInput, TreeSelect,
  Table, DataTable, Tree, TreeList, CheckboxTree, DescriptionList,
  Loading, Modal, MessageBox, SmartTooltip,
  Pagination
} from '@/components';

// 类型同样从统一入口导入
import type {
  TreeSelectProps,
  DescriptionItem,
  MessageBoxOptions,
  MessageBoxType,
  DataTableState
} from '@/components';
```

### 兼容：从 common 直接导入

```typescript
// 仍支持从 common 导入（向后兼容，但不推荐）
import {
  Button, Card,
  Input, Select, DateInput, TreeSelect,
  Table, DataTable, Tree, TreeList, CheckboxTree, DescriptionList
} from '@/components/common';
```

### 按类别导入

```typescript
// 从子目录导入
import { Button, Card } from '@/components/common/general';
import { Input, Select, TreeSelect } from '@/components/common/form';
import { Table, DataTable, Tree } from '@/components/common/data-display';
import { Loading, Modal, MessageBox } from '@/components/common/feedback';
import { Pagination } from '@/components/common/navigation';
```

## MessageBox 服务 API

MessageBox 提供类似 Element Plus 的服务式 API：

```typescript
import { MessageBox } from '@/components/common';

// 确认对话框
const confirmed = await MessageBox.confirm({
  title: '确认删除',
  content: '删除后数据将无法恢复',
  type: 'warning'
});

// 快捷方法
await MessageBox.alert('操作成功');
await MessageBox.success('保存成功');
await MessageBox.error('操作失败');
await MessageBox.info('提示信息');
```

## 统一树类型体系

树组件使用统一的三层类型体系，与后端 TreeNodeMixin 字段命名对齐：

```typescript
import type { TreeNode, TreeNodeTree, TreeSelectNode } from '@/framework/types/tree'
import { toSelectNode, toSelectNodes } from '@/framework/utils/tree'
```

### 类型说明

| 类型 | 用途 | 主要字段 |
|------|------|----------|
| `TreeNode` | API 响应、数据存储（与后端对齐） | `id`, `parent_id`, `name`, `tree_level`, `tree_leaf` |
| `TreeNodeTree` | 树形展示，`buildTree()` 输出 | 继承 TreeNode + `children` |
| `TreeSelectNode` | TreeSelect、CheckboxTree、选择器场景 | `id`, `name`, `children`, `disabled`, `isLeaf` |

### 类型转换

```typescript
// TreeNode → TreeSelectNode
const node = toSelectNode(treeNode)

// TreeNodeTree[] → TreeSelectNode[]（支持嵌套）
const nodes = toSelectNodes(treeNodes)
```

### useTreeData Composable

```typescript
import { useTreeData } from '@/framework/composables/useTreeData'

const { treeData, selectedIds, filteredData, findNode, toggleSelect } = useTreeData({
  source: rawData,
  mode: 'multiple',
  searchable: true,
  defaultExpandLevel: 1,
})
```

### 树组件使用

使用 `Tree` 组件和 `TreeSelectNode` 类型：

```typescript
import { Tree } from '@/components'
import type { TreeSelectNode } from '@/framework/types/tree'
```

## 使用建议

1. **优先使用 common/ 组件**：开发业务页面时，优先查找 common/ 目录
2. **遵循组件分层**：
   - `common/` - 通用业务组件（跨模块复用）— 优先使用
   - `framework/` - 框架层类型、工具、composable — 基础设施
   - `{module}/components/` - 模块专用组件
3. **统一导入入口**：使用 `@/components` 统一入口，便于 tree-shaking
4. **树组件统一使用 TreeSelectNode 类型**：从 `@/framework/types/tree` 导入
