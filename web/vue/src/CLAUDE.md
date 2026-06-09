# Vue 前端开发指南

本文件为 Claude Code 在 Vue 前端源码目录中工作时提供指导。

## 目录定位

`src/` 按顶级模块组织源码。模块是 `src/{module}/`，功能是模块内的子域；不要把功能域提升为新的顶级目录。

## 顶级模块

| 模块 | 定位 | 详细文档 |
|------|------|----------|
| framework | 基础设施：UI框架、路由、状态管理 | [framework/CLAUDE.md](framework/CLAUDE.md) |
| tenant | 租户管理模块 | [tenant/CLAUDE.md](tenant/CLAUDE.md) |
| iam | 身份认证与权限模块 | [iam/CLAUDE.md](iam/CLAUDE.md) |
| ai | AI 对话模块 | [ai/CLAUDE.md](ai/CLAUDE.md) |
| demo | 业务演示模块 | [demo/CLAUDE.md](demo/CLAUDE.md) |
| components | 通用组件（跨模块共享） | 见下方「通用组件清单」 |
| composables | 组合式函数 | - |

## 通用组件清单

组件按层级分为三类，开发功能页面时优先复用已有组件。

### UI 基础组件（ui/）

基于 shadcn/ui 的原子组件，位于 `src/components/ui/`。

| 类别 | 组件 | 说明 |
|------|------|------|
| 基础 | Button, Input, Textarea, Label, Checkbox, Switch, Select | 基础表单控件 |
| 布局 | Card, Separator, Tabs, Accordion, Collapsible | 布局容器 |
| 导航 | Breadcrumb, NavigationMenu, Sidebar | 导航组件 |
| 反馈 | Alert, Progress, Spinner, Skeleton, Tooltip | 反馈提示 |
| 弹层 | Dialog, Popover, Sheet, DropdownMenu, HoverCard | 弹层组件 |
| 数据 | Table, Avatar, Badge | 数据展示 |
| 滚动 | ScrollArea | 滚动容器 |

**导入方式**：
```typescript
import { Button } from '@/components/ui/button/Button.vue';
import { Dialog, DialogContent, DialogHeader } from '@/components/ui/dialog';
```

### 通用业务组件（common/）

位于 `src/components/common/`，按功能分类组织。

| 类别 | 组件 | 用途 |
|------|------|------|
| **通用** | Button, Card | 业务按钮、业务卡片 |
| **表单** | Input, Select, DateInput, TreeSelect | 业务输入框、选择器、日期输入、树选择器 |
| **数据展示** | Table, DataTable, Tree, TreeList, CheckboxTree, DescriptionList | 业务表格、高级表格、树形展示、树形列表、复选框树、描述列表 |
| **反馈** | Loading, Modal, MessageBox, SmartTooltip | 加载状态、业务弹窗、消息框、智能提示 |
| **导航** | Pagination | 分页组件 |

**导入方式**：
```typescript
// 从统一入口导入
import { Button, Card, Input, Select, Table, Tree, Loading, Modal, Pagination } from '@/components/common';

// 导入类型
import type { TreeSelectProps, DescriptionItem, MessageBoxOptions } from '@/components/common';
```

### AI 专用组件（ai-elements/）

专为 AI 对话场景设计，位于 `src/components/ai-elements/`。详见 [ai-elements/CLAUDE.md](components/ai-elements/CLAUDE.md)。

| 类别 | 组件示例 | 用途 |
|------|----------|------|
| 对话核心 | Conversation, Message, MessageContent | 对话容器和消息展示 |
| Agent | Agent, AgentHeader, AgentTools | Agent 展示 |
| 内容展示 | Artifact, CodeBlock, FileTree | 代码、文档展示 |
| 交互反馈 | ChainOfThought, Loader, Shimmer | 思考链、加载状态 |
| 输入组件 | PromptInput, SpeechInput, Attachments | 输入交互 |
| 选择器 | ModelSelector, MicSelector, VoiceSelector | AI 模型/设备选择 |
| 工具调用 | Tool, ToolInput, ToolOutput | 工具调用展示 |
| 引用来源 | InlineCitation, Sources | 引用和来源 |

**导入方式**：
```typescript
import Message from '@/components/ai-elements/message/Message.vue';
import CodeBlock from '@/components/ai-elements/code-block/CodeBlock.vue';
```

## 组件复用查找优先级

开发功能页面时，按以下优先级查找可复用组件：

1. **AI 场景** → 先查 `ai-elements/`（对话、消息、代码块等）
2. **通用业务** → 再查 `common/`（表格、表单、反馈等）
3. **UI 基础** → 最后查 `ui/`（Button, Input, Dialog 等）

## 依赖边界

```
demo / ai / iam / tenant ──▶ framework
framework ──X──▶ demo / ai / iam / tenant
```

- 业务模块可以依赖 `framework`
- `framework` 禁止依赖业务模块
- 跨模块通信通过 Pinia Store、EventBus 或 API 调用

## 模块结构规范

每个业务模块必须包含：

```
src/{module}/
├── index.ts              # 模块入口，导出 ModuleDescriptor
├── router/
│   └── index.ts          # 模块路由配置（必需）
├── api/                  # API 函数
├── types/                # TypeScript 类型定义
├── pages/                # 页面组件
├── components/           # 模块专用组件
└── stores/               # Pinia 状态管理
```

## 组件层级规范

| 层级 | 目录 | 前缀 | 说明 |
|------|------|------|------|
| UI 基础组件 | `src/components/ui/` | 无前缀 | shadcn 组件 |
| 通用业务组件 | `src/components/common/` | 无前缀 | 跨模块共享 |
| AI 专用组件 | `src/components/ai-elements/` | 无前缀 | AI 场景专用 |
| 模块级组件 | `{模块}/components/` | {模块} | 模块专用 |
| 框架级组件 | `framework/components/` | App | 框架功能耦合 |

## 开发约束

- 新模块放在 `src/{module}/`
- 必须在 `index.ts` 导出 `ModuleDescriptor`
- 必须在 `router/index.ts` 定义模块路由
- API 函数使用 `@/framework/api/client` 封装
- Store 使用 Pinia 的 `defineStore` 和 Composition API
- 页面组件使用 `AppPage` 组件作为页面骨架