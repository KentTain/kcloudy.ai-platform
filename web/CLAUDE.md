# CLAUDE.md

本文件为 Claude Code 在前端应用目录工作时提供指导。

## 目录定位

`web/` 目录包含多种前端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范。

## 技术栈状态

| 技术栈 | 语言 | 框架 | 状态 | 详细文档 |
|--------|------|------|------|----------|
| Vue | TypeScript 5.x | Vue 3.5 + Vite 6.x | ✅ 可用 | [vue/CLAUDE.md](vue/CLAUDE.md) |
| React | TypeScript 5.x | React 19 + Vite 6.x | 🚧 规划中 | - |

## 统一项目结构

```text
web/{技术栈}/
├── src/
│   ├── framework/                 # 基础设施层（跨模块共享）
│   │   ├── api/                   # API 客户端
│   │   │   └── client.ts          # - Axios 封装、请求/响应拦截
│   │   ├── stores/                # 全局状态
│   │   │   ├── app.ts             # - 应用状态
│   │   │   ├── user.ts            # - 用户状态
│   │   │   ├── permission.ts      # - 权限状态
│   │   │   └── menu.ts            # - 菜单状态
│   │   ├── types/                 # 公共类型
│   │   │   ├── index.ts           # - 类型入口
│   │   │   └── tree.ts            # - 树节点类型（与后端对齐）
│   │   ├── utils/                 # 工具函数
│   │   │   ├── tree.ts            # - 树工具函数
│   │   │   └── feedback.ts        # - 反馈工具
│   │   ├── composables/           # 组合式函数
│   │   │   ├── usePermission.ts   # - 权限判断
│   │   │   ├── useTreeData.ts     # - 树数据处理
│   │   │   └── useColorMode.ts    # - 主题模式
│   │   ├── layouts/               # 布局组件
│   │   │   ├── AdminLayout.vue    # - 管理布局
│   │   │   └── components/        # - 布局子组件
│   │   ├── pages/                 # 公共页面
│   │   │   ├── LoginPage.vue      # - 登录页
│   │   │   ├── ForbiddenPage.vue  # - 403 页面
│   │   │   └── NotFoundPage.vue   # - 404 页面
│   │   ├── router/                # 路由配置
│   │   │   ├── index.ts           # - 路由实例
│   │   │   └── guards.ts          # - 路由守卫
│   │   ├── directives/            # 自定义指令
│   │   │   └── permission.ts      # - 权限指令
│   │   ├── events/                # 事件总线
│   │   └── module/                # 模块系统
│   │       ├── types.ts           # - 模块协议
│   │       ├── registry.ts        # - 模块注册
│   │       └── setup.ts           # - 模块初始化
│   │
│   ├── components/                # 跨模块共享组件
│   │   ├── ui/                    # UI 基础组件（shadcn）
│   │   ├── common/                # 业务通用组件
│   │   └── ai-elements/           # AI 场景专用组件
│   │
│   ├── composables/               # 全局组合式函数（可选）
│   │
│   └── {module}/                  # 业务模块
│       ├── api/                   # API 函数
│       │   └── conversation.ts    # - 模块 API 封装
│       ├── stores/                # 模块状态
│       │   └── conversation.ts    # - useXxxStore
│       ├── types/                 # 类型定义
│       │   └── index.ts           # - 模块类型
│       ├── composables/           # 组合式函数
│       │   └── useChat.ts         # - useXxx
│       ├── pages/                 # 页面组件
│       │   └── ChatPage.vue       # - XxxPage.vue
│       ├── components/            # 模块专用组件
│       │   └── ModelSelector.vue  # - XxxComponent.vue
│       ├── router/                # 路由配置
│       │   └── index.ts           # - 模块路由
│       └── index.ts               # 模块入口（ModuleDescriptor）
│
└── tests/                         # 测试目录
    ├── components/                # 跨模块组件测试
    │   ├── unit/                  # 单元测试
    │   └── e2e/                   # E2E 测试
    ├── framework/                 # 基础设施测试
    │   ├── unit/
    │   └── e2e/
    └── {module}/                  # 模块测试
        ├── unit/
        └── e2e/
```

## 统一架构及UI组件选型

### 架构规则

| 规则 | 说明 |
|------|------|
| 分层架构 | Screens → Components → Stores → API |
| 模块隔离 | 每个业务模块独立路由和状态 |
| 依赖边界 | 业务模块可依赖 framework，反向禁止 |
| 跨模块通信 | 通过 Pinia Store、EventBus 或 API 调用 |

### UI 组件技术选型

所有前端技术栈采用统一的 UI 组件技术方案：

| 技术层 | Vue | React | 说明 |
|--------|-----|-------|------|
| 组件库 | shadcn-vue | shadcn/ui | 基于 Radix + Tailwind 的组件集 |
| 无样式原语 | Radix Vue | Radix UI | 提供可访问性的底层原语 |
| 样式方案 | Tailwind CSS v4 | Tailwind CSS v4 | 原子化 CSS |

## 层次职责

### 基础设施层（framework/）

| 目录 | 职责 | 说明 |
|------|------|------|
| `api/` | API 客户端 | Axios 封装、请求/响应拦截、Token 注入 |
| `stores/` | 全局状态 | 应用状态、用户状态、权限状态、菜单状态 |
| `types/` | 公共类型 | 跨模块共享类型、与后端对齐的类型定义 |
| `utils/` | 工具函数 | 树工具、反馈工具、通用工具 |
| `composables/` | 组合式函数 | 权限判断、树数据处理、主题模式等可复用逻辑 |
| `layouts/` | 布局组件 | 页面骨架、导航、侧边栏 |
| `pages/` | 公共页面 | 登录页、403、404 等公共页面 |
| `router/` | 路由配置 | 路由实例、路由守卫、静态路由 |
| `directives/` | 自定义指令 | v-permission 等指令 |
| `events/` | 事件总线 | 跨模块事件通信 |
| `module/` | 模块系统 | 模块协议、模块注册、模块初始化 |

### 业务模块层（{module}/）

| 目录 | 职责 | 说明 |
|------|------|------|
| `api/` | API 函数 | 模块相关的 HTTP 请求封装 |
| `stores/` | 模块状态 | Pinia Store，模块级状态管理 |
| `types/` | 类型定义 | 模块相关的 TypeScript 类型 |
| `composables/` | 组合式函数 | 模块级可复用逻辑 |
| `pages/` | 页面组件 | 模块的页面级组件 |
| `components/` | 模块专用组件 | 模块内部复用的组件 |
| `router/` | 路由配置 | 模块路由定义 |
| `index.ts` | 模块入口 | 导出 ModuleDescriptor |

### 跨模块共享组件（components/）

| 目录 | 职责 | 说明 |
|------|------|------|
| `ui/` | UI 基础组件 | shadcn 组件，无业务逻辑 |
| `common/` | 业务通用组件 | 跨模块共享的业务组件 |
| `ai-elements/` | AI 专用组件 | AI 对话场景专用组件 |

## 命名规范

### 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 页面组件 | 大驼峰 + Page | `ChatPage.vue`, `UserListPage.vue` |
| 业务组件 | 大驼峰 | `ModelSelector.vue`, `DatasetCard.vue` |
| 组合式函数 | 小驼峰 + use 前缀 | `useChat.ts`, `useTreeData.ts` |
| Store | 小驼峰 | `conversation.ts`, `user.ts` |
| API 文件 | 小驼峰 | `conversation.ts`, `model.ts` |
| 类型文件 | 小驼峰或 index | `index.ts`, `tree.ts` |
| 工具函数 | 小驼峰 | `tree.ts`, `feedback.ts` |

### 组件命名

| 层级 | 前缀 | 示例 | 说明 |
|------|------|------|------|
| UI 基础组件 | 无前缀 | `Button`, `Dialog` | shadcn 组件，直接使用原名 |
| 业务通用组件 | 可选 Common | `CommonButton` 或 `Button` | 跨模块共享的基础组件 |
| AI 专用组件 | 无前缀 | `Message`, `CodeBlock` | AI 场景专用组件 |
| 模块级组件 | 模块前缀 | `DemoDatasetCard`, `AiModelSelector` | 模块专用组件 |
| 框架级组件 | App | `AppForm`, `AppPage` | 与框架功能耦合的组件 |

### 函数/变量命名

| 类型 | 规范 | 示例 |
|------|------|------|
| Store 定义 | useXxxStore | `useConversationStore`, `useUserStore` |
| API 函数 | 小驼峰 | `getConversations`, `deleteConversation` |
| 类型名称 | 大驼峰 | `TreeNode`, `Conversation`, `ModelConfig` |
| 接口名称 | 大驼峰 + I（可选） | `TreeNode`, `ModuleDescriptor` |
| 事件常量 | 大驼峰 | `USER_LOGGED_IN`, `TENANT_CHANGED` |

### 树结构类型字段命名

| 字段 | 说明 | 示例 |
|------|------|------|
| `parent_id` | 父节点 ID | `parent_id: string \| null` |
| `tree_level` | 树层级 | `tree_level: number` |
| `tree_leaf` | 是否叶子节点 | `tree_leaf: boolean` |
| `tree_sort` | 排序号 | `tree_sort: number` |
| `tree_sorts` | 排序路径 | `tree_sorts: string` |
| `tree_names` | 名称路径 | `tree_names: string` |
| `parent_ids` | 祖先 ID 路径 | `parent_ids: string` |
| `tenant_id` | 租户 ID | `tenant_id: string` |
| `created_at` | 创建时间 | `created_at: string` |
| `updated_at` | 更新时间 | `updated_at: string` |

### 通信对象（DTO）类型命名规范

前后端通信对象的 TypeScript 类型命名遵循以下统一规范：

| 分类 | 命名模式 | 示例 |
|------|----------|------|
| 非分页查询 | `{Entity}Query` | `DepartmentQuery` |
| 分页查询 | `{Entity}PaginatedQuery` | `TenantPaginatedQuery` |
| 新增（创建参数） | `{Entity}Create` | `TenantCreate` |
| 编辑（更新参数） | `{Entity}Update` | `TenantUpdate` |
| 保存（新增或编辑） | `{Entity}Save` | `ConfigSave` |
| 导入 | `{Entity}Import` | `UserImport` |
| 导出 | `{Entity}Export` | `UserExport` |
| 基本响应 | `{Entity}Response` | `TenantResponse` |
| 全量列表响应 | `{Entity}ListResponse` | `MenuListResponse` |
| 分页列表响应 | `{Entity}PaginatedListResponse` | `TenantPaginatedListResponse` |
| 树结构响应 | `{Entity}TreeResponse` | `MenuTreeResponse` |
| 属性/配置响应 | `{Entity}PropertyResponse` | `CachePropertyResponse` |

## 组件导入规范

### 统一入口优先

**优先从 `@/components` 统一入口导入组件**，该入口整合了 common 业务组件和高频 ui 组件：

```typescript
// 推荐：从统一入口导入
import { Button, Input, Badge, Skeleton, Dialog, DialogContent, Tabs, FormField, FormItem } from '@/components'

// 同时支持类型导入
import { Button, type DescriptionItem, type MessageBoxOptions } from '@/components'
```

### 低频组件保持原路径

以下组件不在统一入口，需从 `@/components/ui/xxx` 单独导入：

```typescript
import { Sidebar, SidebarContent } from '@/components/ui/sidebar'
import { Breadcrumb, BreadcrumbItem } from '@/components/ui/breadcrumb'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
```

## API 调用规范

### 路由格式

后端 API 路由遵循 `/{模块}/{类型}/v1/{功能}` 格式：

| 模块 | 类型 | 功能示例 | 完整路径 |
|------|------|---------|---------|
| tenant | admin | tenants | `/tenant/admin/v1/tenants` |
| tenant | console | tenants | `/tenant/console/v1/tenants` |
| iam | console | auth/login | `/iam/console/v1/auth/login` |
| ai | console | chat-messages | `/ai/console/v1/chat-messages` |

### API 客户端配置

API 客户端位于 `framework/api/client.ts`，自动处理：

- Token 注入（JWT Token）
- 请求/响应拦截
- 错误处理
- 租户上下文注入

### 认证策略

| 路径前缀 | 认证方式 |
|---------|---------|
| `/tenant/admin/*` | 租户管理员 Token |
| `/tenant/console/*` | JWT Token |
| `/iam/*` | JWT Token |
| `/ai/*` | JWT Token |

## 测试

测试统一放在各技术栈的 `tests/` 目录下，测试目录按模块进行分类，模块下按测试类型（`unit`、`e2e`）进行划分。

### 测试目录结构

```text
web/{技术栈}/tests/
├── components/              # 跨模块组件测试
│   ├── unit/                # 单元测试
│   └── e2e/                 # E2E 端到端测试
├── framework/               # 基础设施测试
│   ├── unit/
│   └── e2e/
└── {module}/                # 模块测试
    ├── unit/
    └── e2e/
```

### 测试技术栈状态

| 技术栈 | 语言 | 框架 | 状态 | 详细文档 |
|--------|------|------|------|----------|
| Vue | TypeScript 5.x | Vitest, @vue/test-utils, playwright | ✅ 可用 | [vue/tests/CLAUDE.md](vue/tests/CLAUDE.md) |
| React | TypeScript 5.x | React 19 + Vite 6.x | 🚧 规划中 | - |

## 环境要求

- Node.js 22+
- pnpm 10+
