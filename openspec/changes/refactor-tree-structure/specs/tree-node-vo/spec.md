## ADDED Requirements

### Requirement: TreeNodeVo 提供统一的树节点响应格式

`TreeNodeVo` 基类 SHALL 提供统一的树节点字段，用于 API 响应。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | str | 节点ID |
| parent_id | str \| None | 父节点ID |
| tree_level | int | 树层级 |
| tree_leaf | bool | 是否为叶子节点 |
| tree_sort | int | 排序号 |
| tree_sorts | str | 排序路径 |
| tree_names | str | 名称路径 |
| parent_ids | str | 父ID路径 |

#### Scenario: 序列化树节点

- **WHEN** 从 TreeNodeMixin 模型创建 TreeNodeVo
- **THEN** 所有树字段 SHALL 正确映射到 VO

### Requirement: TreeNodeTreeVo 支持嵌套结构

`TreeNodeTreeVo` SHALL 继承 `TreeNodeVo`，增加 children 字段。

#### Scenario: 序列化带子节点的树

- **WHEN** 从树结构创建 TreeNodeTreeVo
- **THEN** children 字段 SHALL 包含子节点列表
- **THEN** children 可以为空列表

#### Scenario: 支持递归序列化

- **WHEN** 树结构有多层嵌套
- **THEN** 所有层级 SHALL 正确序列化
