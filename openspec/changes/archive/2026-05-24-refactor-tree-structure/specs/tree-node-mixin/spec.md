## ADDED Requirements

### Requirement: TreeNodeMixin 提供完整的树字段

`TreeNodeMixin` 混入类 SHALL 为模型提供以下树结构字段：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| parent_id | str | DEFAULT_TREE_ROOT_ID | 父节点ID |
| tree_leaf | bool | True | 是否为叶子节点 |
| tree_level | int | 0 | 树层级 |
| tree_sort | int | 0 | 排序号 |
| tree_sorts | str | "" | 排序路径 |
| tree_names | str | "" | 名称路径 |
| parent_ids | str | DEFAULT_TREE_ROOT_ID, | 父ID路径 |

#### Scenario: 根节点字段初始化

- **WHEN** 创建根层节点（parent_id 为空或 DEFAULT_TREE_ROOT_ID）
- **THEN** tree_level SHALL 为 0
- **THEN** parent_ids SHALL 为 `DEFAULT_TREE_ROOT_ID,`
- **THEN** tree_leaf SHALL 为 True
- **THEN** tree_sorts SHALL 为排序号格式化后的字符串
- **THEN** tree_names SHALL 为节点名称

#### Scenario: 子节点字段初始化

- **WHEN** 创建子节点（parent_id 为有效父节点ID）
- **THEN** tree_level SHALL 为父节点 tree_level + 1
- **THEN** parent_ids SHALL 为 `父节点.parent_ids父节点.id,`
- **THEN** tree_sorts SHALL 为 `父节点.tree_sorts + 当前排序号格式化,`
- **THEN** tree_names SHALL 为 `父节点.tree_names/当前节点名称`

### Requirement: TreeNodeMixin 提供创建节点方法

`TreeNodeMixin` SHALL 提供 `create_node` 类方法，自动维护树字段。

#### Scenario: 创建根节点

- **WHEN** 调用 `create_node(session, {"name": "研发部"})` 且无 parent_id
- **THEN** 创建的节点 parent_id 为 DEFAULT_TREE_ROOT_ID
- **THEN** tree_level 为 0
- **THEN** 自动计算并设置 tree_sort

#### Scenario: 创建子节点

- **WHEN** 调用 `create_node(session, {"name": "前端组", "parent_id": "parent-uuid"})`
- **THEN** 自动设置 tree_level、tree_sorts、tree_names、parent_ids
- **THEN** 父节点的 tree_leaf 设置为 False

#### Scenario: 自动分配排序号

- **WHEN** 创建节点时未指定 tree_sort
- **THEN** 自动分配为同级节点最大排序号 + DEFAULT_SORT

### Requirement: TreeNodeMixin 提供更新节点方法

`TreeNodeMixin` SHALL 提供 `update_node` 类方法，支持移动节点和更新名称。

#### Scenario: 更新节点名称

- **WHEN** 更新节点名称
- **THEN** 自动更新该节点的 tree_names
- **THEN** 级联更新所有子孙节点的 tree_names

#### Scenario: 移动节点到新父节点

- **WHEN** 更新节点的 parent_id
- **THEN** 验证新父节点不是当前节点的子孙节点
- **THEN** 自动更新该节点的 tree_level、tree_sorts、parent_ids
- **THEN** 级联更新所有子孙节点的树字段
- **THEN** 刷新原父节点和新父节点的 tree_leaf 状态

#### Scenario: 阻止循环引用

- **WHEN** 尝试将节点移动到自己的子孙节点下
- **THEN** 抛出 BadRequestError 异常

### Requirement: TreeNodeMixin 提供删除节点方法

`TreeNodeMixin` SHALL 提供 `delete_node` 类方法，支持级联删除。

#### Scenario: 删除叶子节点

- **WHEN** 删除叶子节点
- **THEN** 仅删除该节点
- **THEN** 刷新父节点的 tree_leaf 状态

#### Scenario: 删除非叶子节点

- **WHEN** 删除有子节点的节点
- **THEN** 级联删除所有子孙节点
- **THEN** 返回受影响节点数量

#### Scenario: 软删除支持

- **WHEN** 模型有 deleted_at 字段
- **THEN** 执行软删除（设置 deleted_at）
- **WHEN** 模型无 deleted_at 字段
- **THEN** 执行物理删除

### Requirement: TreeNodeMixin 提供列表查询方法

`TreeNodeMixin` SHALL 提供 `list_nodes` 类方法，返回按 tree_sorts 排序的平铺列表。

#### Scenario: 查询所有节点

- **WHEN** 调用 `list_nodes(session)`
- **THEN** 返回按 tree_sorts 排序的节点列表

#### Scenario: 支持模糊查询

- **WHEN** 调用 `list_nodes(session, fuzzy_fields={"name": "研发"})`
- **THEN** 返回名称包含"研发"的节点列表

### Requirement: TreeNodeMixin 提供树构建方法

`TreeNodeMixin` SHALL 提供 `build_tree` 类方法，将平铺列表转换为树结构。

#### Scenario: 构建完整树

- **WHEN** 调用 `build_tree(nodes)`
- **THEN** 返回树形结构，每个节点包含 children 列表

#### Scenario: 构建子树

- **WHEN** 调用 `build_tree(nodes, parent_id="specific-id")`
- **THEN** 返回以指定节点为根的子树

### Requirement: TreeNodeMixin 支持事件发布

`TreeNodeMixin` SHALL 在节点变更时发布事件。

#### Scenario: 创建节点发布事件

- **WHEN** 成功创建节点
- **THEN** 发布 CREATED 类型事件

#### Scenario: 更新节点发布事件

- **WHEN** 成功更新节点
- **THEN** 发布 UPDATED 类型事件

#### Scenario: 删除节点发布事件

- **WHEN** 成功删除节点
- **THEN** 发布 DELETED 类型事件
