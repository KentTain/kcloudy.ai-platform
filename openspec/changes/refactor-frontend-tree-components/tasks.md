## 1. 类型定义与转换

- [x] 1.1 在 `framework/types/tree.ts` 新增 TreeSelectNode 接口定义
- [x] 1.2 在 `framework/types/tree.ts` 导出 TreeSelectNode 类型
- [x] 1.3 在 `framework/utils/tree.ts` 实现 toSelectNode 函数
- [x] 1.4 在 `framework/utils/tree.ts` 实现 toSelectNodes 函数（支持嵌套）
- [x] 1.5 添加空值处理和边界条件检查

## 2. useTreeData Composable

- [x] 2.1 创建 `framework/composables/useTreeData.ts` 文件
- [x] 2.2 实现数据转换逻辑（字段映射、响应式）
- [x] 2.3 实现选中状态管理（单选/多选、modelValue 同步）
- [x] 2.4 实现搜索过滤逻辑
- [x] 2.5 实现节点查找方法（findNode、getAncestors）
- [x] 2.6 实现选择操作方法（toggleSelect、clearSelection）
- [x] 2.7 导出 composable 并添加类型声明

## 3. 废弃别名与兼容层

- [ ] 3.1 在 `ui/tree/types.ts` 添加 @deprecated TreeNodeType 别名
- [ ] 3.2 在 `ui/tree/types.ts` 添加 @deprecated TreeNode 别名
- [ ] 3.3 从 framework/types/tree 重新导出 TreeSelectNode
- [ ] 3.4 在 `ui/tree/Tree.vue` 添加废弃警告（控制台）

## 4. common/Tree 组件增强

- [ ] 4.1 更新 Tree.vue Props 接口，支持 TreeSelectNode 数据
- [ ] 4.2 新增 checkable/cascade/modelValue Props
- [ ] 4.3 新增 loadData 异步加载支持
- [ ] 4.4 新增 showLine/disabled Props
- [ ] 4.5 实现复选框渲染和级联选择逻辑
- [ ] 4.6 更新 TreeNode.vue 支持新 Props

## 5. common/CheckboxTree 重构

- [ ] 5.1 使用 useTreeData 重构 CheckboxTree.vue
- [ ] 5.2 更新 Props 类型为 TreeSelectNode
- [ ] 5.3 保持原有 API 向后兼容

## 6. common/TreeList 重构

- [ ] 6.1 更新 TreeList.vue 使用 TreeSelectNode 类型
- [ ] 6.2 更新 TreeAction 接口类型

## 7. common/TreeSelect 适配

- [ ] 7.1 更新 TreeSelect.vue Props 使用 TreeSelectNode
- [ ] 7.2 内部使用 toSelectNodes 转换数据

## 8. 业务组件迁移

- [ ] 8.1 DepartmentTree.vue 使用 useTreeData 重构
- [ ] 8.2 MenuTree.vue 使用 useTreeData 重构
- [ ] 8.3 PermissionTree.vue 使用 useTreeData 重构
- [ ] 8.4 移除各组件中的重复代码（数据转换、查找逻辑）

## 9. 测试

- [ ] 9.1 编写 toSelectNode/toSelectNodes 单元测试
- [ ] 9.2 编写 useTreeData 单元测试
- [ ] 9.3 编写 common/Tree 新增功能测试
- [ ] 9.4 运行现有组件测试确保向后兼容
- [ ] 9.5 编写业务组件迁移后的集成测试

## 10. 文档更新

- [ ] 10.1 更新 `framework/types/tree.ts` 的 JSDoc 注释
- [ ] 10.2 更新 `components/common/CLAUDE.md` 说明统一类型用法
- [ ] 10.3 创建迁移指南文档
