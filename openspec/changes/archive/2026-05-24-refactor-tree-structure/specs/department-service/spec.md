## MODIFIED Requirements

### Requirement: DepartmentService 使用 TreeNodeMixin 方法

`DepartmentService` SHALL 使用 `TreeNodeMixin` 提供的方法，简化业务逻辑。

#### Scenario: 创建部门

- **WHEN** 调用 `DepartmentService.create()`
- **THEN** 内部调用 `Department.create_node()`
- **THEN** 树字段自动维护

#### Scenario: 更新部门

- **WHEN** 调用 `DepartmentService.update()`
- **THEN** 内部调用 `Department.update_node()`
- **THEN** 级联更新子孙部门

#### Scenario: 删除部门

- **WHEN** 调用 `DepartmentService.delete()`
- **THEN** 内部调用 `Department.delete_node()`
- **THEN** 级联删除子部门

#### Scenario: 获取部门树

- **WHEN** 调用 `DepartmentService.get_tree()`
- **THEN** 内部调用 `Department.list_nodes()` 获取平铺列表
- **THEN** 内部调用 `Department.build_tree()` 构建树结构

### Requirement: 移除手动树构建逻辑

`DepartmentService` SHALL 移除以下手动逻辑：

- 手动构建树结构的 `_build_tree_fields` 方法
- 手动刷新子孙节点的 `_refresh_descendants` 方法
- 手动处理父节点叶子状态的逻辑

#### Scenario: 代码简化

- **WHEN** 重构完成
- **THEN** DepartmentService 代码行数减少 50% 以上
- **THEN** 无手动树字段维护代码
