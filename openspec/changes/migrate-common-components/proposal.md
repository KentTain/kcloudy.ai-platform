# Common 组件迁移方案

## Why

当前 `web/vue` 项目存在两组通用组件：
1. **Common 系列**：扁平结构放置在 `components/` 根目录，命名使用 `Common` 前缀（CommonButton、CommonTable 等）
2. **Alon 系列**：参考项目中的组件，功能更完善

现有 Common 组件存在以下问题：
- 扁平结构不利于扩展，随着组件增多将难以维护
- 命名前缀 `Common` 冗余，不符合语义化命名惯例
- 部分组件功能简单（如 CommonTable 仅支持 slot 模式），缺乏高级功能
- Alon 项目中的 DataTable、MessageBox、SmartTooltip、TreeSelect 等组件功能更完善

本项目旨在重组通用组件目录结构，迁移 Alon 项目优秀组件，建立清晰的组件分层体系。

## What Changes

### 新增能力

- **分层目录结构**：按功能类型组织组件（form/data-display/feedback/navigation/general）
- **DataTable**：基于 @tanstack/vue-table 的高级表格组件，支持远程数据、分页、骨架屏
- **MessageBox**：服务式 API 消息框，支持 Promise 链式调用
- **SmartTooltip**：智能溢出检测提示组件
- **TreeSelect**：功能完整的树形选择器

### 修改内容

- **BREAKING** 删除所有 `Common` 前缀，使用语义化命名
- **BREAKING** 组件迁移至分层目录结构
- 新增 `ui/tree/` 基础树组件（从 Alon 项目迁移）
- 新增依赖 `@chenglou/pretext` 用于 SmartTooltip 文本测量

## Capabilities

### New Capabilities

- `common-data-table`: 高级数据表格（@tanstack/vue-table、分页、骨架屏）
- `common-message-box`: 服务式消息框（Promise API）
- `common-smart-tooltip`: 智能溢出检测提示
- `common-tree-select`: 树形选择器（搜索/多选/级联/异步加载）
- `ui-tree`: 基础树组件原语

### Modified Capabilities

- `common-components`: Common 组件重组至分层目录结构，语义化命名

## Impact

### 受影响代码

| 路径 | 影响类型 |
|------|----------|
| `web/vue/src/components/common/` | 新增分层目录结构 |
| `web/vue/src/components/ui/tree/` | 新增基础树组件 |
| `web/vue/src/components/Common*.vue` | 删除旧组件 |
| `web/vue/package.json` | 新增 @chenglou/pretext 依赖 |

### 依赖变更

新增依赖：
- `@chenglou/pretext@0.0.7`：用于 SmartTooltip 文本溢出检测

现有依赖（已满足）：
- `@tanstack/vue-table@^8.21.3`：DataTable 核心
- `lucide-vue-next`：图标库
- `shadcn-vue`：UI 原语

### 兼容性考虑

- 旧组件直接删除，不做向后兼容
- 迁移后导出策略使用命名导出，便于 tree-shaking
