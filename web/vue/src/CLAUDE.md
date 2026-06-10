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

## 组件导入规范

### 统一入口

**优先从 `@/components` 统一入口导入组件**，该入口整合了 common 业务组件和高频 ui 组件：

```typescript
// 推荐：从统一入口导入
import { Button, Input, Badge, Skeleton, Dialog, DialogContent, Tabs, FormField, FormItem } from '@/components'

// 同时支持类型导入
import { Button, type DescriptionItem, type MessageBoxOptions } from '@/components'
```

### 统一入口组件清单

| 来源 | 组件 | 说明 |
|------|------|------|
| common | Button, Card, Input, Select, Table, Tree, TreeList, CheckboxTree, DescriptionList, Loading, Modal, MessageBox, SmartTooltip, Pagination, DateInput, TreeSelect, DataTable, DataTablePagination | 业务封装组件，同名覆盖 ui 版本 |
| ui 重导出 | Badge, Skeleton, Label, Checkbox, Switch, Textarea | 高频基础组件 |
| ui 重导出 | Dialog/DialogClose/DialogContent/... | 弹窗复合组件 |
| ui 重导出 | Tabs/TabsContent/TabsList/TabsTrigger | 标签页复合组件 |
| ui 重导出 | Form/FormField/FormItem/FormLabel/FormControl/FormMessage | 表单复合组件 |

### 低频组件保持原路径

以下组件不在统一入口，需从 `@/components/ui/xxx` 单独导入：

```typescript
import { Sidebar, SidebarContent } from '@/components/ui/sidebar'
import { Breadcrumb, BreadcrumbItem } from '@/components/ui/breadcrumb'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { DropdownMenu, DropdownMenuContent } from '@/components/ui/dropdown-menu'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Collapsible, CollapsibleContent } from '@/components/ui/collapsible'
import { Separator } from '@/components/ui/separator'
import { Accordion, AccordionItem } from '@/components/ui/accordion'
import { HoverCard, HoverCardContent } from '@/components/ui/hover-card'
import { Tooltip, TooltipContent } from '@/components/ui/tooltip'
import { Command, CommandInput } from '@/components/ui/command'
import { Popover, PopoverContent } from '@/components/ui/popover'
import { Progress } from '@/components/ui/progress'
import { Spinner } from '@/components/ui/spinner'
```

### 特殊组件：Tree

**ui/Tree 与 common/Tree 数据结构不兼容**，需根据场景选择：

```typescript
// 简单展示树（click/toggle 事件）→ 从统一入口导入
import { Tree } from '@/components'

// 功能树（checkbox/cascade/异步加载）→ 从 ui 路径导入
import { Tree } from '@/components/ui/tree'
import type { TreeNodeType } from '@/components/ui/tree'
```

### 手动组装型组件

Card/Select/Table 在 ui/ 和 common/ 中 API 模式不同：

- **common 版本**：声明式 API（如 `options`、`columns`），一步到位
- **ui 版本**：手动组装子组件（如 CardContent、SelectItem、TableBody）

如果页面使用手动组装方式，保持从 `ui/xxx` 导入：

```typescript
// 手动组装 Card → 保持 ui 路径
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

// 使用 common Card 封装 → 从统一入口导入
import { Card } from '@/components'
```

## 通用组件清单

组件按层级分为三类，开发功能页面时优先复用已有组件。

### 通用业务组件（common/）

位于 `src/components/common/`，按功能分类组织，位于 `src/components/common/`。详见 [common/CLAUDE.md](components/common/CLAUDE.md)。

| 类别 | 组件 | 用途 |
|------|------|------|
| **通用** | Button, Card | 业务按钮、业务卡片 |
| **表单** | Input, Select, DateInput, TreeSelect | 业务输入框、选择器、日期输入、树选择器 |
| **数据展示** | Table, DataTable, Tree, TreeList, CheckboxTree, DescriptionList | 业务表格、高级表格、树形展示、树形列表、复选框树、描述列表 |
| **反馈** | Loading, Modal, MessageBox, SmartTooltip | 加载状态、业务弹窗、消息框、智能提示 |
| **导航** | Pagination | 分页组件 |

**导入方式**：

```typescript
// 推荐：从统一入口导入
import { Button, Card, Input, Select, Table, Tree, Loading, Modal, Pagination } from '@/components';

// 导入类型
import type { TreeSelectProps, DescriptionItem, MessageBoxOptions } from '@/components';

// 兼容：仍可从 @/components/common 导入（但不推荐）
import { Button, Card } from '@/components/common';
```

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
// 高频组件：从统一入口导入（推荐）
import { Badge, Skeleton, Label, Checkbox, Switch, Textarea } from '@/components';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components';
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components';

// 低频组件：从 ui 路径导入
import { Sidebar, SidebarContent } from '@/components/ui/sidebar';
import { Breadcrumb, BreadcrumbItem } from '@/components/ui/breadcrumb';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Command, CommandInput } from '@/components/ui/command';
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

1. **统一入口** → 先从 `@/components` 导入（覆盖 90% 场景）
2. **AI 场景** → 再查 `@/components/ai-elements/`（对话、消息、代码块等）
3. **低频 UI** → 最后查 `@/components/ui/xxx`（sidebar、breadcrumb 等）

**快速判断**：
- 业务按钮/输入框/表格 → `@/components`
- 弹窗/标签页/表单验证 → `@/components`
- 徽章/骨架屏/开关 → `@/components`
- 侧边栏/面包屑/头像 → `@/components/ui/xxx`
- AI 对话相关 → `@/components/ai-elements/xxx`

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
| 通用业务组件 | `src/components/common/` | 无前缀 | 跨模块共享 |
| UI 基础组件 | `src/components/ui/` | 无前缀 | shadcn 组件 |
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
