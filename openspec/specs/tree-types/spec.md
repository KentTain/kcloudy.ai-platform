# tree-types

## Purpose

tree-types 定义前端树节点的 TypeScript 接口，包括 TreeNode（平铺节点）、TreeNodeTree（嵌套节点）和 TreeComponentNode（简化展示节点），确保前后端数据结构的一致性。

## Requirements

### Requirement: TreeNode 接口定义

`TreeNode` 接口 SHALL 定义前端树节点的基本结构。

```typescript
interface TreeNode {
  id: string;
  parent_id: string | null;
  name: string;
  tree_level: number;
  tree_leaf: boolean;
  tree_sort: number;
  tree_sorts: string;
  tree_names: string;
  parent_ids: string;
}
```

#### Scenario: 类型兼容性

- **WHEN** 后端返回树节点数据
- **THEN** 前端 TreeNode 接口 SHALL 能够正确接收

### Requirement: TreeNodeTree 接口定义

`TreeNodeTree` 接口 SHALL 继承 `TreeNode`，增加 children 字段。

```typescript
interface TreeNodeTree extends TreeNode {
  children?: TreeNodeTree[];
}
```

#### Scenario: 树形数据结构

- **WHEN** 前端接收树形 API 响应
- **THEN** TreeNodeTree 接口 SHALL 正确描述嵌套结构

### Requirement: TreeComponentNode 接口定义

`TreeComponentNode` 接口 SHALL 定义简化版树节点，用于纯展示组件。

```typescript
interface TreeComponentNode {
  id: string | number;
  name: string;
  children?: TreeComponentNode[];
  [key: string]: any;
}
```

#### Scenario: 组件通用性

- **WHEN** 树组件仅需要 id/name/children
- **THEN** SHALL 使用 TreeComponentNode 接口