# ui-tree 规格

## 概述

基础树组件原语，为 TreeSelect 等上层组件提供树渲染能力。

## 功能需求

### 核心功能

- 树节点渲染
- 展开/折叠
- 单选/多选
- 复选框模式
- 级联选择
- 异步加载
- 自定义节点图标

### 组件 API

#### Tree

**Props:**

```typescript
interface TreeProps {
  data?: TreeNode[]
  modelValue?: any[]
  multiple?: boolean
  checkable?: boolean
  cascade?: boolean
  showLine?: boolean
  dark?: boolean
  expandOnRowClick?: boolean
  expandedValue?: TreeNodeValue[]
  loadData?: (node: TreeNode, callback: (children: TreeNode[]) => void) => void
}
```

**Events:**

```typescript
{
  'update:modelValue': [value: any[]]
  'update:expandedValue': [value: TreeNodeValue[]]
  'on-expand': [node: TreeNode]
  'on-node-click': [node: TreeNode]
  'on-load': [node: TreeNode]
}
```

**Slots:**

- label：节点标签
- expand：展开图标
- collapse：折叠图标
- leaf-icon：叶节点图标

#### TreeNode

内部组件，递归渲染树节点。

### 类型定义

```typescript
interface TreeNode {
  label: string
  value?: any
  children?: TreeNode[]
  disabled?: boolean
  selected?: boolean
  isLeaf?: boolean
}

type TreeNodeValue = TreeNode['value']
```

## 迁移来源

- 源文件：`D:\Project\ai\Alon\apps\kbhub\web\src\components\ui\shadcn-tree\`
- 目标位置：`web/vue/src/components/ui/tree/`

## 文件清单

| 源文件 | 目标文件 |
|--------|----------|
| ShadcnTree.vue | Tree.vue |
| ShadcnTreeNode.vue | TreeNode.vue |
| types.ts | types.ts |
| index.ts | index.ts |

## 验收标准

- [ ] 组件迁移完成，文件位置正确
- [ ] 重命名完成（移除 Shadcn 前缀）
- [ ] 类型定义完整
- [ ] 构建通过
