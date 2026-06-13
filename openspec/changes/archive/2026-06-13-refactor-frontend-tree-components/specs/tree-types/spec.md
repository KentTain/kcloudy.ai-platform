## 新增需求

### 需求:TreeNode 基础类型定义

系统必须提供与后端 TreeNodeMixin 字段完全对齐的 TreeNode 类型定义，用于 API 响应和数据存储。

#### 场景:TreeNode 包含所有树字段
- **当** 开发者使用 TreeNode 类型
- **那么** 类型包含 id, parent_id, name, tree_level, tree_leaf, tree_sort, tree_sorts, tree_names, parent_ids 字段

#### 场景:TreeNode 字段类型正确
- **当** 开发者检查 TreeNode 字段类型
- **那么** id 为 string, parent_id 为 string | null, tree_level 为 number, tree_leaf 为 boolean

### 需求:TreeNodeTree 嵌套类型定义

系统必须提供 TreeNodeTree 类型，继承 TreeNode 并添加 children 属性，用于树形数据展示。

#### 场景:TreeNodeTree 包含 children
- **当** 开发者使用 TreeNodeTree 类型
- **那么** 类型包含 TreeNode 所有字段，以及可选的 children: TreeNodeTree[] 属性

### 需求:TreeSelectNode 选择器类型定义

系统必须提供 TreeSelectNode 类型，用于 TreeSelect 和带选择的树组件，字段命名与 TreeNode 对齐。

#### 场景:TreeSelectNode 包含基础字段
- **当** 开发者使用 TreeSelectNode 类型
- **那么** 类型包含 id (string | number), name (string), children (可选), disabled (可选), isLeaf (可选) 字段

#### 场景:TreeSelectNode 允许扩展字段
- **当** 开发者需要添加自定义字段
- **那么** 类型允许通过泛型或索引签名扩展

### 需求:类型转换函数

系统必须提供 toSelectNode 和 toSelectNodes 转换函数，将 TreeNode 转换为 TreeSelectNode 格式。

#### 场景:单个节点转换
- **当** 开发者调用 toSelectNode(treeNode)
- **那么** 返回 TreeSelectNode，其中 id = treeNode.id, name = treeNode.name, isLeaf = treeNode.tree_leaf

#### 场景:嵌套节点转换
- **当** 开发者调用 toSelectNodes([treeNodeWithChildren])
- **那么** 递归转换所有子节点，返回 TreeSelectNode[]

#### 场景:空节点处理
- **当** 开发者调用 toSelectNode(null 或 undefined)
- **那么** 返回 null 而不抛出异常

### 需求:废弃类型别名

系统必须在 ui/tree/types.ts 中提供废弃类型别名，保持向后兼容。

#### 场景:TreeNodeType 别名可用
- **当** 开发者从 ui/tree/types 导入 TreeNodeType
- **那么** 类型等同于 TreeSelectNode，IDE 显示 @deprecated 警告

#### 场景:TreeNode 别名可用（ui 上下文）
- **当** 开发者从 ui/tree/types 导入 TreeNode
- **那么** 类型等同于 TreeSelectNode，IDE 显示 @deprecated 警告

## 修改需求

(无)

## 移除需求

(无)
