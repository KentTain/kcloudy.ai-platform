# common-tree-select 规格

## 概述

功能完整的树形选择器，支持搜索、多选、级联选择、异步加载。

## 功能需求

### 核心功能

- 单选/多选模式
- 搜索过滤
- 级联选择
- 异步加载子节点
- 清空选择
- 自定义对齐方式

### 组件 API

**Props:**

```typescript
interface TreeSelectProps {
  modelValue?: TreeSelectValue | TreeSelectValue[] | null
  data: TreeNode[]
  multiple?: boolean
  checkable?: boolean
  cascade?: boolean
  searchable?: boolean
  clearable?: boolean
  disabled?: boolean
  placeholder?: string
  emptyText?: string
  loading?: boolean
  loadingText?: string
  sameWidth?: boolean
  align?: 'start' | 'center' | 'end'
  showLine?: boolean
  expandedValue?: TreeNodeValue[]
  loadData?: (node: TreeNode, callback: (children: TreeNode[]) => void) => void
}
```

**Events:**

```typescript
{
  'update:modelValue': [value: TreeSelectValue | TreeSelectValue[] | null]
  'update:expandedValue': [value: TreeNodeValue[]]
  'search': [query: string]
  'on-node-click': [node: TreeNode]
}
```

## 迁移来源

- 源文件：`D:\Project\ai\Alon\apps\kbhub\web\src\components\alon\alon-tree-select\`
- 目标位置：`web/vue/src/components/common/form/tree-select/`

## 文件清单

| 源文件 | 目标文件 |
|--------|----------|
| AlonTreeSelect.vue | TreeSelect.vue |
| index.ts | index.ts |

## 依赖

- ui/popover
- ui/tree（Tree 基础组件）
- lucide-vue-next（ChevronDown, Search, X）

## 验收标准

- [ ] 组件迁移完成，文件位置正确
- [ ] 重命名完成（移除 Alon 前缀）
- [ ] 导入 ui/tree 路径正确
- [ ] 构建通过
