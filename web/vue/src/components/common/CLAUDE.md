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
| Tree | `data-display/tree/Tree.vue` | 树形展示 | `data`, `defaultExpandLevel`, `indent` |
| TreeList | `data-display/tree/TreeList.vue` | 树形列表（带操作按钮） | `data`, `actions`, `defaultExpandLevel` |
| CheckboxTree | `data-display/tree/CheckboxTree.vue` | 复选框树 | `data`, `modelValue`, `searchable`, `disabled` |
| DescriptionList | `data-display/description-list/DescriptionList.vue` | 描述列表 | `items`, `columns`, `bordered` |

### 反馈组件（feedback/）

| 组件 | 文件 | 用途 | 主要 Props |
|------|------|------|------------|
| Loading | `feedback/loading/Loading.vue` | 加载状态 | `size`, `text`, `fullscreen` |
| Modal | `feedback/modal/Modal.vue` | 业务弹窗 | `modelValue`, `title`, `size`, `closable`, `maskClosable` |
| MessageBox | `feedback/message-box/MessageBox.vue` | 消息框（服务式 API） | `title`, `content`, `type`, `showCancel` |
| SmartTooltip | `feedback/tooltip/SmartTooltip.vue` | 智能溢出提示 | `content`, `contentClass`, `onlyEllipsisOpen` |

### 导航组件（navigation/）

| 组件 | 文件 | 用途 | 主要 Props |
|------|------|------|------------|
| Pagination | `navigation/pagination/Pagination.vue` | 分页组件 | `total`, `page`, `pageSize`, `pageSizeOptions` |

## 导入方式

### 从统一入口导入

```typescript
import {
  Button, Card,
  Input, Select, DateInput, TreeSelect,
  Table, DataTable, Tree, TreeList, CheckboxTree, DescriptionList,
  Loading, Modal, MessageBox, SmartTooltip,
  Pagination
} from '@/components/common';
```

### 导入类型

```typescript
import type {
  TreeSelectProps,
  DescriptionItem,
  MessageBoxOptions,
  MessageBoxType,
  DataTableState
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

## 基础树组件（ui/tree/）

`ui/tree/` 提供基础树组件原语，被 TreeSelect 等上层组件复用：

```typescript
import { Tree, TreeNode } from '@/components/ui/tree';
import type { TreeNode as TreeNodeType, TreeProps } from '@/components/ui/tree';
```

## 使用建议

1. **优先使用 common/ 组件**：开发业务页面时，优先查找 common/ 目录
2. **遵循组件分层**：
   - `ui/` - 基础 UI 原语（无业务逻辑）
   - `common/` - 通用业务组件（跨模块复用）
   - `{module}/components/` - 模块专用组件
3. **统一导入入口**：使用 `@/components/common` 统一入口，便于 tree-shaking
