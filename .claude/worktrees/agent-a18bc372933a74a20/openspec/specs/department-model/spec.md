# department-model

## Purpose

Department 模型继承 TreeNodeMixin，获得完整的树结构支持，包括树字段的自动维护和级联更新能力。

## Requirements

### Requirement: Department 模型继承 TreeNodeMixin

`Department` 模型 SHALL 继承 `TreeNodeMixin`，获得完整的树结构支持。

#### 原有字段

| 字段 | 类型 | 说明 |
|------|------|------|
| tenant_id | str | 租户ID |
| name | str | 部门名称 |
| code | str | None | 部门编码 |
| sort_order | int | 排序号 |
| leader_id | str | None | 部门负责人ID |
| status | str | 状态 |

#### 新增字段（来自 TreeNodeMixin）

| 字段 | 类型 | 说明 |
|------|------|------|
| parent_id | str | 父部门ID |
| tree_leaf | bool | 是否为叶子节点 |
| tree_level | int | 层级 |
| tree_sort | int | 排序号（映射自 sort_order） |
| tree_sorts | str | 排序路径 |
| tree_names | str | 名称路径 |
| parent_ids | str | 父ID路径 |

#### Scenario: 部门创建

- **WHEN** 创建部门
- **THEN** 自动维护所有树字段

#### Scenario: 部门更新

- **WHEN** 更新部门名称或父部门
- **THEN** 自动更新 tree_names 或级联更新子孙部门

#### Scenario: 部门删除

- **WHEN** 删除部门
- **THEN** 级联删除所有子部门

#### Scenario: 树名称字段

- **WHEN** 调用 `tree_name_field()`
- **THEN** 返回 "name"