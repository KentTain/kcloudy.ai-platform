# 树组件迁移指南

## 概述

前端树组件已完成统一重构。迁移到新的类型和 API 以获得更好的类型安全和更少的重复代码。

## 迁移步骤

### 1. 类型迁移

```typescript
// 旧（废弃）
import type { TreeNodeType } from '@/components/ui/tree'

// 新（推荐）
import type { TreeSelectNode } from '@/framework/types/tree'
```

### 2. 字段映射

| 旧字段 | 新字段 | 说明 |
|--------|--------|------|
| `value` | `id` | 字符串或数字 |
| `label` | `name` | 显示文本 |
| `selected` | 使用组件 `modelValue` | 不再作为节点属性 |
| `isLeaf` | `isLeaf` | 不变 |

### 3. 组件迁移

```vue
<!-- 旧 -->
<script setup lang="ts">
import { Tree } from '@/components/ui/tree'
import type { TreeNodeType } from '@/components/ui/tree'
const treeData = ref<TreeNodeType[]>([...])
</script>
<template>
  <Tree :data="treeData" />
</template>

<!-- 新 -->
<script setup lang="ts">
import { Tree } from '@/components'
import type { TreeSelectNode } from '@/framework/types/tree'
const treeData = ref<TreeSelectNode[]>([...])
</script>
<template>
  <Tree :data="treeData" />
</template>
```

### 4. 使用 useTreeData（推荐）

```vue
<script setup lang="ts">
import { useTreeData } from '@/framework/composables/useTreeData'

const { treeData, selectedIds, filteredData, findNode, toggleSelect } = useTreeData({
  source: () => props.data,
  modelValue: () => props.modelValue,
  mode: 'multiple',
  searchable: true,
  defaultExpandLevel: 1,
})
</script>
<template>
  <Tree
    :data="filteredData"
    checkable
    cascade
    v-model="selectedIds"
  />
</template>
```

### 5. CheckboxTree 迁移

```vue
<!-- 新 CheckboxTree 直接使用 useTreeData -->
<script setup lang="ts">
import { CheckboxTree } from '@/components'
import type { TreeSelectNode } from '@/framework/types/tree'

const data = ref<TreeSelectNode[]>([...])
const selectedIds = ref<(string | number)[]>([])
</script>
<template>
  <CheckboxTree
    :data="data"
    v-model="selectedIds"
    searchable
  />
</template>
```

## 新增功能

### Tree 组件

| 功能 | 用法 |
|------|------|
| 复选框选择 | `<Tree checkable v-model="selectedIds" />` |
| 级联选择 | `<Tree checkable cascade v-model="selectedIds" />` |
| 异步加载 | `<Tree :loadData="handleLoadData" />` |
| 连接线 | `<Tree showLine />` |
| 禁用状态 | `<Tree disabled />` |

### toSelectNode / toSelectNodes

```typescript
import { toSelectNode, toSelectNodes } from '@/framework/utils/tree'

// 单个节点转换
const selectNode = toSelectNode(treeNode)

// 嵌套转换
const selectNodes = toSelectNodes(treeNodes)
```

## 常见问题

**Q: 现有代码需要立即迁移吗？**
A: 不需要。`ui/tree/types.ts` 提供了 @deprecated 别名，现有代码可以继续工作。IDE 会显示迁移提示。

**Q: TreeComponentNode 还能用吗？**
A: 可以用，但 `TreeComponentNode` 已标记 @deprecated。新代码推荐使用 `TreeSelectNode`。

**Q: useTreeData 是否必须使用？**
A: 不必须，但强烈推荐。它消除了数据转换、选中状态管理、搜索过滤的重复代码。
