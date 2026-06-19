## Why

当前项目的树结构实现存在以下问题：

1. **字段不完整**：`TreeMixin` 仅提供 `parent_id`、`level`、`path` 三个字段，缺少 `tree_sorts`（排序路径）、`tree_names`（名称路径）、`parent_ids`（父ID路径）、`tree_leaf`（叶子标记）等关键字段，导致排序、查询、路径追踪能力不足。

2. **CRUD 支持缺失**：没有内置的树节点 CRUD 方法，每个业务模块都需要手动实现创建、更新、删除、列表查询逻辑，代码重复且容易出错。

3. **级联更新困难**：更新父节点时，子孙节点的路径字段无法自动同步维护，需要业务代码手动处理。

4. **前后端不一致**：后端树字段与前端 `TreeNode` 接口不对应，前端组件定制化程度高，难以复用。

参考 Alon 项目的 `TreeNodeMixin` 实现，可以系统性地解决这些问题。

## What Changes

### 后端 Python

- **重构 `framework/database/mixins/tree.py`**：重写为完整的 `TreeNodeMixin`，包含 7 个树字段和完整的 CRUD 方法
- **新增 `framework/core/constants.py`**：树相关常量定义
- **新增 `framework/schemas/tree.py`**：`TreeNodeVo` / `TreeNodeTreeVo` 基类
- **简化 `framework/utils/tree_util.py`**：删除重复逻辑，保留通用构建方法
- **更新 `iam/models/department.py`**：继承 `TreeNodeMixin`
- **更新 `iam/schemas/department.py`**：继承 `TreeNodeVo` 基类
- **简化 `iam/services/department_service.py`**：使用 `TreeNodeMixin` 内置方法
- **新增数据库迁移**：为 `departments` 表添加树字段

### 前端 Vue

- **新增 `framework/types/tree.ts`**：树节点接口定义
- **新增 `framework/utils/tree.ts`**：树工具函数
- **新增 `components/CommonTree.vue`**：基础展示树组件
- **新增 `components/CommonSelectTree.vue`**：下拉选择树组件
- **新增 `components/CommonTreeList.vue`**：列表树组件
- **重构 `components/CommonCheckboxTree.vue`**：继承 `CommonTree`
- **更新 `iam/types/index.ts`**：`Department` 继承 `TreeNode`
- **更新 `iam/components/DepartmentTree.vue`**：使用新组件

### 文档更新

- 更新 `framework/CLAUDE.md`、`iam/CLAUDE.md`、`components/CLAUDE.md` 等文档

## Capabilities

### New Capabilities

- `tree-node-mixin`：后端树节点混入类，提供完整的树字段和 CRUD 方法
- `tree-node-vo`：后端树节点 VO 基类，统一的树节点响应格式
- `tree-types`：前端树节点类型定义
- `tree-utils`：前端树工具函数
- `common-tree-components`：通用树组件（CommonTree、CommonSelectTree、CommonTreeList）

### Modified Capabilities

- `department-model`：部门模型继承 `TreeNodeMixin`，增加树字段
- `department-service`：部门服务使用 `TreeNodeMixin` 内置方法

## Impact

### 受影响的后端模块

- `framework/database/mixins/`：树混入类重写
- `framework/schemas/`：新增树 VO 基类
- `iam/models/`：部门模型字段变更
- `iam/services/`：部门服务逻辑简化
- `iam/migrations/`：新增迁移脚本

### 受影响的前端模块

- `framework/types/`：新增树类型定义
- `framework/utils/`：新增树工具函数
- `components/`：新增/重构树组件
- `iam/types/`：部门类型更新
- `iam/components/`：部门树组件更新

### 数据库影响

- `departments` 表新增字段：`tree_leaf`、`tree_level`、`tree_sort`、`tree_sorts`、`tree_names`、`parent_ids`
- 需要迁移脚本为现有数据填充新字段

### API 兼容性

- 部门 API 响应将包含新的树字段，向后兼容（新增字段）
- 现有 `parent_id` 字段行为不变
