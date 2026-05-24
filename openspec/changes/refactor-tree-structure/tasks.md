## 1. 后端基础设施

- [x] 1.1 创建 `framework/core/constants.py`，定义树相关常量（DEFAULT_SORT、TREE_SORTS_LENGTH、TREE_SORTS_PADSTR、DEFAULT_TREE_ROOT_ID）
- [x] 1.2 重写 `framework/database/mixins/tree.py`，实现完整的 `TreeNodeMixin`（7个字段 + CRUD方法 + 事件发布）
- [x] 1.3 创建 `framework/schemas/tree.py`，定义 `TreeNodeVo` 和 `TreeNodeTreeVo` 基类
- [x] 1.4 简化 `framework/utils/tree_util.py`，删除重复逻辑，保留 `build_tree` 方法
- [x] 1.5 更新 `framework/database/__init__.py`，导出新的 `TreeNodeMixin`

## 2. 后端业务模块集成

- [x] 2.1 更新 `iam/models/department.py`，继承 `TreeNodeMixin`
- [x] 2.2 更新 `iam/schemas/department.py`，`DepartmentVo` 继承 `TreeNodeVo`，`DepartmentTreeVo` 继承 `TreeNodeTreeVo`
- [x] 2.3 简化 `iam/services/department_service.py`，使用 `TreeNodeMixin` 内置方法
- [x] 2.4 创建数据库迁移脚本，为 `departments` 表添加树字段
- [x] 2.5 编写迁移数据填充脚本，为现有部门数据填充树字段

## 3. 前端基础设施

- [x] 3.1 创建 `framework/types/tree.ts`，定义 `TreeNode`、`TreeNodeTree`、`TreeComponentNode` 接口
- [x] 3.2 创建 `framework/utils/tree.ts`，实现 `buildTree`、`flattenTree`、`findNodeById`、`getAncestors`、`sortByTreeSorts` 函数
- [x] 3.3 更新 `framework/types/index.ts`，导出树类型

## 4. 前端组件开发

- [x] 4.1 创建 `components/CommonTree.vue`，实现基础展示树组件
- [x] 4.2 重构 `components/CommonCheckboxTree.vue`，继承 `CommonTree` 的基础能力
- [x] 4.3 创建 `components/CommonSelectTree.vue`，实现下拉选择树组件
- [x] 4.4 创建 `components/CommonTreeList.vue`，实现列表树组件

## 5. 前端业务模块集成

- [x] 5.1 更新 `iam/types/index.ts`，`Department` 继承 `TreeNode` 接口（IAM 前端模块尚未创建，跳过）
- [x] 5.2 更新 `iam/components/DepartmentTree.vue`，使用新组件和类型（IAM 前端模块尚未创建，跳过）

## 6. 文档更新

- [x] 6.1 更新 `server/python/src/framework/CLAUDE.md`，添加树结构模块说明
- [x] 6.2 更新 `server/python/src/iam/CLAUDE.md`，添加部门模型树字段说明
- [x] 6.3 更新 `web/vue/src/CLAUDE.md`，添加树类型和工具说明
- [x] 6.4 更新 `web/vue/src/components/CLAUDE.md`，添加树组件说明
- [x] 6.5 更新 `web/vue/src/framework/CLAUDE.md`，添加树类型和工具文档

## 7. 测试验证

- [x] 7.1 编写后端 `TreeNodeMixin` 单元测试（14个测试，全部通过）
- [x] 7.2 编写前端树工具函数单元测试（10个测试，全部通过）
- [x] 7.3 编写前端树组件测试（3个测试，全部通过）
- [ ] 7.4 执行数据库迁移验证
- [ ] 7.5 执行部门 API 集成测试
