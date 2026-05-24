## ADDED Requirements

### Requirement: buildTree 函数

`buildTree` 函数 SHALL 将平铺列表转换为树结构。

```typescript
function buildTree<T extends TreeNode>(
  nodes: T[],
  parentId: string | null = null
): TreeNodeTree[];
```

#### Scenario: 构建完整树

- **WHEN** 传入平铺节点列表
- **THEN** 返回树形结构，每个节点包含 children 数组

#### Scenario: 构建子树

- **WHEN** 传入 parentId 参数
- **THEN** 仅返回以该 parentId 为根的子树

#### Scenario: 空列表处理

- **WHEN** 传入空数组
- **THEN** 返回空数组

### Requirement: flattenTree 函数

`flattenTree` 函数 SHALL 将树结构转换为平铺列表。

```typescript
function flattenTree<T extends TreeNodeTree>(tree: T[]): T[];
```

#### Scenario: 扁平化树

- **WHEN** 传入树形结构
- **THEN** 返回平铺列表，保留所有节点

#### Scenario: 保持顺序

- **WHEN** 扁平化树
- **THEN** 节点顺序 SHALL 按 tree_sorts 排序

### Requirement: findNodeById 函数

`findNodeById` 函数 SHALL 在树中查找指定节点。

```typescript
function findNodeById<T extends TreeNodeTree>(
  tree: T[],
  id: string
): T | undefined;
```

#### Scenario: 查找存在的节点

- **WHEN** 节点存在于树中
- **THEN** 返回该节点

#### Scenario: 查找不存在的节点

- **WHEN** 节点不存在于树中
- **THEN** 返回 undefined

### Requirement: getAncestors 函数

`getAncestors` 函数 SHALL 获取指定节点的所有祖先节点。

```typescript
function getAncestors<T extends TreeNode>(
  nodes: T[],
  nodeId: string
): T[];
```

#### Scenario: 获取祖先节点

- **WHEN** 传入节点ID
- **THEN** 返回从根节点到父节点的祖先列表

#### Scenario: 根节点无祖先

- **WHEN** 传入根节点ID
- **THEN** 返回空数组

### Requirement: sortByTreeSorts 函数

`sortByTreeSorts` 函数 SHALL 按 tree_sorts 字段排序节点。

```typescript
function sortByTreeSorts<T extends TreeNode>(nodes: T[]): T[];
```

#### Scenario: 排序节点列表

- **WHEN** 传入无序节点列表
- **THEN** 返回按 tree_sorts 排序的列表
