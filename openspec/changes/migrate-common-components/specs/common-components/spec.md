# common-components 规格

## 概述

Common 组件重组至分层目录结构，语义化命名。

## 目录结构

```
web/vue/src/components/common/
├── form/                              # 表单类组件
│   ├── input/
│   │   ├── Input.vue
│   │   └── index.ts
│   ├── select/
│   │   ├── Select.vue
│   │   └── index.ts
│   ├── tree-select/
│   │   ├── TreeSelect.vue
│   │   └── index.ts
│   ├── date-input/
│   │   ├── DateInput.vue
│   │   └── index.ts
│   └── index.ts
│
├── data-display/                      # 数据展示类组件
│   ├── table/
│   │   ├── Table.vue
│   │   ├── DataTable.vue
│   │   ├── DataTablePagination.vue
│   │   ├── use-data-table.ts
│   │   └── index.ts
│   ├── tree/
│   │   ├── Tree.vue
│   │   ├── TreeList.vue
│   │   ├── CheckboxTree.vue
│   │   └── index.ts
│   ├── description-list/
│   │   ├── DescriptionList.vue
│   │   └── index.ts
│   └── index.ts
│
├── feedback/                          # 反馈类组件
│   ├── loading/
│   │   ├── Loading.vue
│   │   └── index.ts
│   ├── modal/
│   │   ├── Modal.vue
│   │   └── index.ts
│   ├── message-box/
│   │   ├── MessageBox.vue
│   │   ├── messageBox.ts
│   │   └── index.ts
│   ├── tooltip/
│   │   ├── SmartTooltip.vue
│   │   └── index.ts
│   └── index.ts
│
├── navigation/                        # 导航类组件
│   ├── pagination/
│   │   ├── Pagination.vue
│   │   └── index.ts
│   └── index.ts
│
├── general/                           # 通用组件
│   ├── button/
│   │   ├── Button.vue
│   │   └── index.ts
│   ├── card/
│   │   ├── Card.vue
│   │   └── index.ts
│   └── index.ts
│
└── index.ts                           # 总导出
```

## 导出策略

使用命名导出：

```typescript
// common/index.ts
export { Button } from './general/button'
export { Card } from './general/card'
export { Input, Select, TreeSelect, DateInput } from './form'
export { Table, DataTable, Tree, TreeList, CheckboxTree, DescriptionList } from './data-display'
export { Loading, Modal, MessageBox } from './feedback'
export { Pagination } from './navigation'
```

## 组件迁移映射

| 源组件 | 目标位置 |
|--------|----------|
| CommonButton.vue | general/button/Button.vue |
| CommonCard.vue | general/card/Card.vue |
| CommonInput.vue | form/input/Input.vue |
| CommonSelect.vue | form/select/Select.vue |
| CommonSelectTree.vue | 合并到 TreeSelect |
| CommonDateInput.vue | form/date-input/DateInput.vue |
| CommonTable.vue | data-display/table/Table.vue |
| CommonTree.vue | data-display/tree/Tree.vue |
| CommonTreeList.vue | data-display/tree/TreeList.vue |
| CommonCheckboxTree.vue | data-display/tree/CheckboxTree.vue |
| CommonDescriptionList.vue | data-display/description-list/DescriptionList.vue |
| CommonLoading.vue | feedback/loading/Loading.vue |
| CommonModal.vue | feedback/modal/Modal.vue |
| CommonPagination.vue | navigation/pagination/Pagination.vue |

## 验收标准

- [ ] 目录结构创建完成
- [ ] 所有组件迁移完成
- [ ] 重命名完成（移除 Common 前缀）
- [ ] 索引文件创建完成
- [ ] 旧组件删除完成
- [ ] 构建通过
