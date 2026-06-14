## 为什么

前端树组件统一重构已完成（2026-06-13），`common/Tree` 已具备 `checkable/cascade/loadData` 全部功能。遗留的 `ui/tree` 目录和 `TreeComponentNode` 类型已标记 `@deprecated`，现在可以安全移除，减少维护负担和代码混淆。

## 变更内容

- **移除** `web/vue/src/components/ui/tree/` 目录（Tree.vue、TreeNode.vue、types.ts、index.ts）
- **移除** `framework/types/tree.ts` 中的 `TreeComponentNode` 类型
- **迁移** `tenant/pages/admin/ModuleDetail.vue` 使用 `common/Tree` 和 `TreeSelectNode` 类型
- **更新** 测试文件 `tests/framework/unit/utils/tree.test.ts` 使用 `TreeSelectNode` 替代 `TreeComponentNode`
- **更新** 相关文档（CLAUDE.md）中的示例代码

## 功能 (Capabilities)

### 新增功能

无。这是清理工作，不引入新功能。

### 修改功能

无。规范层面无行为变更，仅移除废弃实现。

## 影响

| 类别 | 影响范围 |
|------|----------|
| 代码 | `web/vue/src/components/ui/tree/` 目录删除 |
| 代码 | `framework/types/tree.ts` 移除 `TreeComponentNode` |
| 代码 | `ModuleDetail.vue` 需迁移 import 和类型 |
| 测试 | `tree.test.ts` 需更新测试数据类型 |
| 文档 | 多处 CLAUDE.md 引用需更新 |
| API | 无影响 |
| 兼容性 | 无破坏性变更（废弃代码已有替代方案） |
