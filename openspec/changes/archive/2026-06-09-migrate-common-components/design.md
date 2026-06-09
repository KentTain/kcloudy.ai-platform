# Common 组件迁移技术设计

## Context

### 当前状态

`web/vue` 项目现有组件结构：
- `components/Common*.vue`：14 个扁平结构的通用组件
- `components/ui/`：shadcn-vue 基础组件库
- `components/ai-elements/`：AI 专用组件库

参考项目（Alon）组件：
- `alon-table`：基于 @tanstack/vue-table 的高级表格
- `alon-message-box`：服务式 API 消息框
- `alon-tooltip`：智能溢出检测提示
- `alon-tree-select`：功能完整的树形选择器
- `ui/shadcn-tree/`：基础树组件原语

### 约束

- 不保留旧组件兼容性，直接删除
- 导出策略使用命名导出
- 基础树组件放置在 `ui/tree/`
- 不迁移样式文件（本次仅迁移组件）

## Goals / Non-Goals

**Goals:**

1. 建立分层目录结构（form/data-display/feedback/navigation/general）
2. 迁移 Common 系列组件，语义化重命名
3. 迁移 Alon DataTable、MessageBox、SmartTooltip、TreeSelect
4. 迁移基础树组件至 `ui/tree/`
5. 统一导出接口

**Non-Goals:**

1. 样式迁移（用户明确不迁移）
2. 组件功能增强（仅迁移，不重构）
3. 测试迁移（后续单独任务）

## Decisions

### 1. 目录结构方案

**决策**：采用分层目录结构，按功能类型组织

**目录结构**：

```
web/vue/src/components/common/
├── form/                              # 表单类组件
│   ├── input/
│   │   ├── Input.vue                  # 迁移自 CommonInput
│   │   └── index.ts
│   ├── select/
│   │   ├── Select.vue                 # 迁移自 CommonSelect
│   │   └── index.ts
│   ├── tree-select/
│   │   ├── TreeSelect.vue             # 迁移自 AlonTreeSelect
│   │   └── index.ts
│   ├── date-input/
│   │   ├── DateInput.vue              # 迁移自 CommonDateInput
│   │   └── index.ts
│   └── index.ts
│
├── data-display/                      # 数据展示类组件
│   ├── table/
│   │   ├── Table.vue                  # 迁移自 CommonTable（简化版）
│   │   ├── DataTable.vue              # 迁移自 AlonDataTable（高级版）
│   │   ├── DataTablePagination.vue    # 迁移自 AlonDataTablePagination
│   │   ├── use-data-table.ts          # 迁移自 use-alon-table.ts
│   │   └── index.ts
│   ├── tree/
│   │   ├── Tree.vue                   # 迁移自 CommonTree
│   │   ├── TreeList.vue               # 迁移自 CommonTreeList
│   │   ├── CheckboxTree.vue           # 迁移自 CommonCheckboxTree
│   │   └── index.ts
│   ├── description-list/
│   │   ├── DescriptionList.vue        # 迁移自 CommonDescriptionList
│   │   └── index.ts
│   └── index.ts
│
├── feedback/                          # 反馈类组件
│   ├── loading/
│   │   ├── Loading.vue                # 迁移自 CommonLoading
│   │   └── index.ts
│   ├── modal/
│   │   ├── Modal.vue                  # 迁移自 CommonModal
│   │   └── index.ts
│   ├── message-box/
│   │   ├── MessageBox.vue             # 迁移自 AlonMessageBox
│   │   ├── messageBox.ts              # 服务层
│   │   └── index.ts
│   ├── tooltip/
│   │   ├── SmartTooltip.vue           # 迁移自 AlonTooltip
│   │   └── index.ts
│   └── index.ts
│
├── navigation/                        # 导航类组件
│   ├── pagination/
│   │   ├── Pagination.vue             # 迁移自 CommonPagination
│   │   └── index.ts
│   └── index.ts
│
├── general/                           # 通用组件
│   ├── button/
│   │   ├── Button.vue                 # 迁移自 CommonButton
│   │   └── index.ts
│   ├── card/
│   │   ├── Card.vue                   # 迁移自 CommonCard
│   │   └── index.ts
│   └── index.ts
│
└── index.ts                           # 总导出
```

### 2. 基础树组件放置方案

**决策**：放置在 `ui/tree/`，与 `ui/button`, `ui/table` 同级

**理由**：
- 符合 shadcn-vue 组织方式
- 作为基础组件原语，可被上层组件复用
- 与其他 UI 原语保持一致

**目录结构**：

```
web/vue/src/components/ui/tree/
├── Tree.vue                           # 迁移自 ShadcnTree.vue
├── TreeNode.vue                       # 迁移自 ShadcnTreeNode.vue
├── types.ts                           # 迁移自 shadcn-tree/types.ts
└── index.ts
```

### 3. 导出策略

**决策**：命名导出

**实现**：

```typescript
// common/index.ts
export { Button } from './general/button'
export { Card } from './general/card'
export { Input, Select, TreeSelect, DateInput } from './form'
export { Table, DataTable, Tree, TreeList, CheckboxTree, DescriptionList } from './data-display'
export { Loading, Modal, MessageBox } from './feedback'
export { Pagination } from './navigation'

// 使用方式
import { Button, DataTable, MessageBox } from '@/components/common'
```

### 4. 组件迁移映射

| 源组件 | 目标位置 | 新命名 |
|--------|----------|--------|
| CommonButton.vue | general/button/ | Button |
| CommonCard.vue | general/card/ | Card |
| CommonInput.vue | form/input/ | Input |
| CommonSelect.vue | form/select/ | Select |
| CommonSelectTree.vue | 合并到 TreeSelect | - |
| CommonDateInput.vue | form/date-input/ | DateInput |
| CommonTable.vue | data-display/table/ | Table |
| CommonTree.vue | data-display/tree/ | Tree |
| CommonTreeList.vue | data-display/tree/ | TreeList |
| CommonCheckboxTree.vue | data-display/tree/ | CheckboxTree |
| CommonDescriptionList.vue | data-display/description-list/ | DescriptionList |
| CommonLoading.vue | feedback/loading/ | Loading |
| CommonModal.vue | feedback/modal/ | Modal |
| CommonPagination.vue | navigation/pagination/ | Pagination |
| AlonDataTable.vue | data-display/table/ | DataTable |
| AlonDataTablePagination.vue | data-display/table/ | DataTablePagination |
| use-alon-table.ts | data-display/table/ | use-data-table.ts |
| AlonMessageBox.vue | feedback/message-box/ | MessageBox |
| messageBox.ts | feedback/message-box/ | messageBox.ts |
| AlonTooltip.vue | feedback/tooltip/ | SmartTooltip |
| AlonTreeSelect.vue | form/tree-select/ | TreeSelect |
| ShadcnTree.vue | ui/tree/ | Tree |
| ShadcnTreeNode.vue | ui/tree/ | TreeNode |

### 5. 依赖管理

**新增依赖**：
- `@chenglou/pretext@0.0.7`：SmartTooltip 文本测量

**现有依赖**（已满足）：
- `@tanstack/vue-table@^8.21.3`
- `lucide-vue-next`
- `reka-ui`

## Risks / Trade-offs

### 风险 1：导入路径变更

**风险**：现有代码可能引用旧组件路径

**缓解措施**：
- 旧组件未被使用（codegraph 验证）
- 如有遗漏，编译时报错易于发现

### 风险 2：类型定义迁移

**风险**：TreeSelect、DataTable 类型定义可能遗漏

**缓解措施**：
- 迁移时同步迁移 types.ts 文件
- 编译时类型检查

### 风险 3：测试文件更新

**风险**：现有测试引用旧组件路径

**缓解措施**：
- 测试文件同步更新
- 运行测试验证

## Migration Plan

### 阶段 1：创建目录结构

1. 创建 `components/common/` 分层目录
2. 创建 `components/ui/tree/` 目录

### 阶段 2：迁移 Common 组件

1. 迁移 general 类组件（Button, Card）
2. 迁移 form 类组件（Input, Select, DateInput）
3. 迁移 data-display 类组件（Table, Tree, TreeList, CheckboxTree, DescriptionList）
4. 迁移 feedback 类组件（Loading, Modal）
5. 迁移 navigation 类组件（Pagination）

### 阶段 3：迁移 Alon 组件

1. 迁移基础树组件至 `ui/tree/`
2. 迁移 DataTable 相关文件
3. 迁移 MessageBox 相关文件
4. 迁移 SmartTooltip
5. 迁移 TreeSelect

### 阶段 4：删除旧组件

1. 删除 `components/Common*.vue`
2. 更新导入路径

### 阶段 5：添加依赖

1. 安装 `@chenglou/pretext@0.0.7`

### 阶段 6：验证

1. 运行构建验证
2. 运行类型检查
3. 运行测试验证

### 6. 组件文档策略

**决策**：分层文档策略

**理由**：
- 开发者需要快速发现可用组件
- AI 助手需要感知组件清单以提供智能建议
- 上层文档提供导航，组件目录提供详细手册

**实现结构**：

**web/vue/src/CLAUDE.md 添加章节**：

```markdown
## 通用组件清单

### UI 基础组件（shadcn-vue）

| 组件 | 目录 | 用途 |
|------|------|------|
| Button | ui/button/ | 按钮基础组件 |
| Input | ui/input/ | 输入框基础组件 |
| Dialog | ui/dialog/ | 对话框基础组件 |
| Table | ui/table/ | 表格原语（无状态） |
| Tooltip | ui/tooltip/ | 提示框基础组件 |
| ... | ... | ... |

### 通用业务组件（common）

| 组件 | 目录 | 用途 | 文档 |
|------|------|------|------|
| Button | common/general/button/ | 带尺寸/变体预设的按钮 | - |
| Input | common/form/input/ | 带清空/错误提示的输入框 | - |
| Select | common/form/select/ | 下拉选择器 | - |
| TreeSelect | common/form/tree-select/ | 树形选择器 | [spec](...) |
| DataTable | common/data-display/table/ | 高级数据表格 | [spec](...) |
| MessageBox | common/feedback/message-box/ | 服务式消息框 | [spec](...) |
| SmartTooltip | common/feedback/tooltip/ | 智能溢出提示 | [spec](...) |
| ... | ... | ... | ... |

### AI 专用组件（ai-elements）

| 组件 | 目录 | 用途 |
|------|------|------|
| Message | ai-elements/message/ | 聊天消息组件 |
| PromptInput | ai-elements/prompt-input/ | 提示词输入框 |
| CodeBlock | ai-elements/code-block/ | 代码块渲染 |
| ... | ... | ... |

**使用方式**：

```typescript
// 从统一入口导入
import { Button, DataTable, MessageBox } from '@/components/common'
import { Dialog, Table } from '@/components/ui/dialog'
import { Message } from '@/components/ai-elements/message'
```
```

**components/common/CLAUDE.md 内容**：

- 组件详细文档（Props/用法/示例）
- 按功能分类（form/data-display/feedback/navigation/general）

**components/ai-elements/CLAUDE.md 内容**：

- AI 组件清单
- 用途说明
- 导入示例
