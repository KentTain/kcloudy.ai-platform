# Common 组件迁移任务

## 1. 创建目录结构

- [x] 1.1 创建 `web/vue/src/components/common/` 分层目录结构
- [x] 1.2 创建 `web/vue/src/components/ui/tree/` 目录

## 2. 迁移基础树组件至 ui/tree/

- [x] 2.1 迁移 ShadcnTree.vue → Tree.vue
- [x] 2.2 迁移 ShadcnTreeNode.vue → TreeNode.vue
- [x] 2.3 迁移 types.ts
- [x] 2.4 创建 index.ts 导出

## 3. 迁移 general 类组件

- [x] 3.1 迁移 CommonButton.vue → general/button/Button.vue
- [x] 3.2 迁移 CommonCard.vue → general/card/Card.vue
- [x] 3.3 创建 general/index.ts

## 4. 迁移 form 类组件

- [ ] 4.1 迁移 CommonInput.vue → form/input/Input.vue
- [ ] 4.2 迁移 CommonSelect.vue → form/select/Select.vue
- [ ] 4.3 迁移 CommonDateInput.vue → form/date-input/DateInput.vue
- [ ] 4.4 迁移 AlonTreeSelect.vue → form/tree-select/TreeSelect.vue
- [ ] 4.5 创建 form/index.ts

## 5. 迁移 data-display 类组件

- [ ] 5.1 迁移 CommonTable.vue → data-display/table/Table.vue
- [ ] 5.2 迁移 AlonDataTable.vue → data-display/table/DataTable.vue
- [ ] 5.3 迁移 AlonDataTablePagination.vue → data-display/table/DataTablePagination.vue
- [ ] 5.4 迁移 use-alon-table.ts → data-display/table/use-data-table.ts
- [ ] 5.5 迁移 CommonTree.vue → data-display/tree/Tree.vue
- [ ] 5.6 迁移 CommonTreeList.vue → data-display/tree/TreeList.vue
- [ ] 5.7 迁移 CommonCheckboxTree.vue → data-display/tree/CheckboxTree.vue
- [ ] 5.8 迁移 CommonDescriptionList.vue → data-display/description-list/DescriptionList.vue
- [ ] 5.9 创建 data-display/index.ts

## 6. 迁移 feedback 类组件

- [ ] 6.1 迁移 CommonLoading.vue → feedback/loading/Loading.vue
- [ ] 6.2 迁移 CommonModal.vue → feedback/modal/Modal.vue
- [ ] 6.3 迁移 AlonMessageBox.vue → feedback/message-box/MessageBox.vue
- [ ] 6.4 迁移 messageBox.ts → feedback/message-box/messageBox.ts
- [ ] 6.5 迁移 AlonTooltip.vue → feedback/tooltip/SmartTooltip.vue
- [ ] 6.6 创建 feedback/index.ts

## 7. 迁移 navigation 类组件

- [ ] 7.1 迁移 CommonPagination.vue → navigation/pagination/Pagination.vue
- [ ] 7.2 创建 navigation/index.ts

## 8. 创建总导出

- [ ] 8.1 创建 `web/vue/src/components/common/index.ts` 命名导出

## 9. 删除旧组件

- [ ] 9.1 删除 `web/vue/src/components/Common*.vue` 所有文件

## 10. 添加依赖

- [ ] 10.1 安装 `@chenglou/pretext@0.0.7` 依赖

## 11. 验证

- [ ] 11.1 运行 `pnpm build` 验证构建
- [ ] 11.2 运行 `pnpm type-check` 验证类型
- [ ] 11.3 运行 `pnpm test:unit` 验证测试

## 12. 补充组件文档

- [ ] 12.1 在 web/vue/src/CLAUDE.md 添加「通用组件清单」章节
  - UI 基础组件清单（ui/）
  - 通用业务组件清单（common/）
  - AI 专用组件清单（ai-elements/）
  - 导入方式说明
- [ ] 12.2 创建 web/vue/src/components/common/CLAUDE.md 组件详细文档
  - 组件清单表格（组件/用途/Props）
  - 按功能分类（form/data-display/feedback/navigation/general）
  - 导入示例
- [ ] 12.3 创建 web/vue/src/components/ai-elements/CLAUDE.md AI 组件文档
  - AI 组件清单
  - 用途说明
  - 导入示例
