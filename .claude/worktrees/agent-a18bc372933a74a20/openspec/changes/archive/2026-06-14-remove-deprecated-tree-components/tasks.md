## 1. 迁移 ModuleDetail.vue

- [x] 1.1 修改 import 语句：`Tree` 从 `@/components` 导入，`TreeSelectNode` 从 `@/framework/types/tree` 导入
- [x] 1.2 重写 `convertToTreeNode` 函数，使用新字段 `id/name` 替代 `value/label`
- [x] 1.3 更新 `handleMenuNodeClick` 参数类型为 `TreeSelectNode`
- [x] 1.4 验证模块详情页面功能正常

## 2. 更新测试文件

- [x] 2.1 修改 `tests/framework/unit/utils/tree.test.ts` 中 `TreeComponentNode` 为 `TreeSelectNode`
- [x] 2.2 运行单元测试确认通过

## 3. 删除废弃代码

- [x] 3.1 删除 `web/vue/src/components/ui/tree/` 目录（Tree.vue、TreeNode.vue、types.ts、index.ts）
- [x] 3.2 删除 `framework/types/tree.ts` 中的 `TreeComponentNode` 接口
- [x] 3.3 运行类型检查确认无编译错误

## 4. 更新文档

- [x] 4.1 更新 `web/vue/src/CLAUDE.md` 中 tree 组件相关示例
- [x] 4.2 更新 `web/vue/src/components/common/CLAUDE.md` 中的废弃引用
- [x] 4.3 全局搜索并清理 `ui/tree` 和 `TreeNodeType` 的剩余引用

## 5. 验证

- [x] 5.1 运行 `pnpm check` 确认无 lint 错误
- [x] 5.2 运行 `pnpm test:unit` 确认所有测试通过
- [ ] 5.3 手动验证模块详情页菜单树功能
