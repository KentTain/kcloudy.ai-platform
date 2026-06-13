## 为什么

前端树组件存在三方面问题：
1. **类型定义分散**：`ui/tree/types.ts` 和 `framework/types/tree.ts` 两套不兼容的类型，业务组件需要重复编写转换逻辑
2. **组件职责重叠**：`ui/Tree` 和 `common/Tree` 功能边界模糊，API 差异大（value/label vs id/name），开发者难以选择
3. **业务组件重复**：DepartmentTree、MenuTree、PermissionTree 内部逻辑高度相似（数据转换、选中管理、节点查找），维护成本高

后端已有统一的 TreeNodeMixin 模型，前端应当与之对齐，通过 composable 抽取通用逻辑，消除重复代码。

## 变更内容

### 统一数据结构
- 采用三层类型体系：TreeNode（与后端对齐）→ TreeNodeTree（嵌套）→ TreeSelectNode（选择器）
- 废弃 `ui/tree/types.ts` 中的 TreeNodeType，提供 @deprecated 别名保持兼容

### 合并树组件
- 增强 `common/Tree` 覆盖 `ui/Tree` 的核心能力（checkbox、cascade、loadData）
- `ui/Tree` 标记废弃，引导开发者迁移到 `common/Tree`
- 统一 Props API：使用 `id/name/children` 替代 `value/label`

### 抽取 useTreeData composable
- 数据转换：配置化字段映射
- 状态管理：选中值同步（modelValue）、展开状态
- 搜索过滤：关键词过滤树节点
- 节点查找：复用 framework/utils/tree.ts

### 消除业务组件重复
- DepartmentTree、MenuTree、PermissionTree 使用 useTreeData
- 仅保留业务特化逻辑（如 PermissionTree 的分组）

**BREAKING**: `ui/Tree` 的 TreeNodeType 类型废弃，Props `value/label` 改为 `id/name`

## 功能 (Capabilities)

### 新增功能

- `tree-types`: 统一的树类型定义体系（TreeNode、TreeNodeTree、TreeSelectNode），与后端模型对齐，包含类型定义和转换工具函数
- `use-tree-data`: 树数据管理 composable，提供数据转换、选中状态、搜索过滤、节点查找能力

### 修改功能

- `common-tree-components`: Tree/CheckboxTree/TreeList 组件增强，支持 checkbox/cascade/loadData，统一 Props API
- `tree-component`: 现有 Tree 组件的 Props 接口和类型定义

## 影响

**受影响文件**：
- `web/vue/src/framework/types/tree.ts` — 新增 TreeSelectNode 类型
- `web/vue/src/framework/utils/tree.ts` — 新增 toSelectNode() 转换函数
- `web/vue/src/framework/composables/useTreeData.ts` — 新增 composable
- `web/vue/src/components/ui/tree/types.ts` — 标记废弃，添加类型别名
- `web/vue/src/components/ui/tree/Tree.vue` — 标记废弃
- `web/vue/src/components/common/data-display/tree/*.vue` — 增强 Props API
- `web/vue/src/components/common/form/tree-select/TreeSelect.vue` — 适配新类型
- `web/vue/src/iam/components/*Tree.vue` — 使用 useTreeData 重构

**API 影响**：
- 无后端 API 变更
- 前端组件 Props 保持向后兼容（提供废弃别名）

**依赖影响**：
- 无新增外部依赖
