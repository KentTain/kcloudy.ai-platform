# Vue 前端开发指南

本文件为 Claude Code 在 Vue 前端源码目录中工作时提供指导。

## 目录结构

```text
src/
├── components/                # 通用组件
│   ├── ui/                    # UI 基础组件（CommonButton、CommonInput 等）
│   └── common/                # 通用业务组件（预留）
├── composables/               # 组合式函数（useAsync、useDebounce 等）
├── demo/                      # Demo 业务模块
├── tenant/                    # Tenant 租户管理模块
├── iam/                       # IAM 身份认证与权限模块
├── framework/                 # Framework UI框架模块
└── lib/                       # 工具库
```

## 架构特性

- **模块级路由隔离**：每个业务模块拥有独立的路由配置（`router/index.ts`）
- **模块动态加载**：通过 `ModuleDescriptor` 描述符声明模块信息，支持按需加载
- **模块依赖管理**：模块可声明依赖关系，注册时自动验证依赖是否满足

## 模块结构规范

每个业务模块应包含以下关键文件：

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

### 模块描述符 (index.ts)

每个模块必须定义 `ModuleDescriptor`，实现模块声明：

```typescript
import type { ModuleDescriptor } from "@/framework/module/types";
import { moduleRoutes } from "./router";

export const myModule: ModuleDescriptor = {
  name: "my_module",           // 模块名称，小写字母、数字、连字符
  version: "1.0.0",            // 模块版本，遵循 semver
  getRoutes: () => moduleRoutes, // 返回路由配置（必需）
  dependencies: [],            // 依赖的其他模块名称
  icon: "module-icon",         // 模块图标标识
  getMenuItems: () => [...],   // 返回菜单项
  getStores: () => ({...}),    // 返回 Store 对象
  setup: async (app, pinia) => {
    // 模块初始化逻辑
  },
};

export * from "./api";
export * from "./types";
```

### 模块路由配置 (router/index.ts)

```typescript
import type { RouteRecordRaw } from "vue-router";

export const moduleRoutes: RouteRecordRaw[] = [
  {
    path: "resources",
    name: "ResourceList",
    component: () => import("@/module/pages/ResourceList.vue"),
    meta: {
      title: "资源管理",
      icon: "database",
      requiresAuth: true,
      roles: ["admin"]
    },
  },
];

export default moduleRoutes;
```

路由元信息说明：

| 属性 | 类型 | 说明 |
|------|------|------|
| `title` | string | 页面标题，用于面包屑和 TagsView |
| `icon` | string | 菜单图标标识 |
| `hidden` | boolean | 是否隐藏菜单项 |
| `requiresAuth` | boolean | 是否需要登录 |
| `roles` | string[] | 允许访问的角色列表 |

### 模块状态管理 (stores/)

```typescript
// stores/index.ts
import { useResourceStore } from "./resource";

export const useModuleStores = () => ({
  resource: useResourceStore(),
});
```

## 开发约定

- 新模块放在 `src/{module}/`，不要放在 `src/core/`、`src/common/` 等跨模块目录；可复用基础能力应进入 `framework/`。
- **必须** 在新模块中创建 `index.ts` 导出 `ModuleDescriptor`。
- **必须** 在模块 `router/index.ts` 中定义模块路由，使用 `meta` 标注权限和标题。
- 业务模块可以依赖 framework；framework 禁止依赖业务模块。
- 跨模块数据引用通过 API 调用或 Pinia Store 共享，不直接导入其他模块内部实现。
- 模块路由、Store、类型应与模块代码同目录维护。
- API 函数使用 `@/framework/api/client` 的封装方法，不直接使用 axios。
- Store 使用 Pinia 的 `defineStore` 和 Composition API。
- 页面组件使用 `AppPage` 组件作为页面骨架。

## 模块边界与依赖

```
demo / iam / tenant ──▶ framework
framework ──X──▶ demo / iam / tenant
```

- **依赖方向**：业务模块可以依赖 framework；framework 禁止依赖业务模块。
- **跨模块通信**：通过 Pinia Store、EventBus 或 API 调用，不直接导入其他模块内部实现。
- **共享组件**：跨模块共享的组件放入 `components/`，模块专用组件保留在 `{模块}/components/`。

## 功能模块

| 模块 | 说明 | 详细文档 |
|------|------|----------|
| components | 业务无关的通用组件，可在任意模块使用 | 见下方"组件体系" |
| composables | Vue 3 组合式函数，封装可复用的响应式逻辑 | 见下方"Composables" |
| demo | 业务演示模块：健康检查、知识库管理 | [demo/CLAUDE.md](demo/CLAUDE.md) |
| tenant | 租户管理模块：租户创建、切换、配置 | [tenant/CLAUDE.md](tenant/CLAUDE.md) |
| iam | 身份认证与权限模块：用户、角色、权限管理 | [iam/CLAUDE.md](iam/CLAUDE.md) |
| framework | 基础设施：UI框架、路由、状态管理、AppPage 页面骨架、树类型与工具 | [framework/CLAUDE.md](framework/CLAUDE.md) |

## 组件体系

### 组件层级与命名

| 层级 | 目录 | 前缀 | 示例 | 说明 |
|------|------|------|------|------|
| 技术栈通用组件 | `src/components/ui/` | `Common` | `CommonButton` | 跨模块共享的基础组件 |
| 模块级通用组件 | `{模块}/components/` | `{模块}` | `DemoDatasetCard` | 模块专用组件 |
| 框架级组件 | `framework/components/` | `App` | `AppForm` | 与框架功能耦合的组件 |

### 常用通用组件

| 组件 | 用途 |
|------|------|
| CommonButton、CommonInput、CommonModal | 基础 UI 组件 |
| CommonTree、CommonCheckboxTree、CommonSelectTree | 树组件体系 |
| CommonTable、CommonSelect | 数据展示与选择 |

### 组件开发规范

- 使用 `<script setup lang="ts">` 语法
- Props 使用 `defineProps` + `withDefaults`
- Emits 使用 `defineEmits`
- 样式使用 scoped CSS，优先使用 Tailwind 类

## Composables

常用组合式函数：

| 函数 | 说明 | 用途 |
|------|------|------|
| `useAsync` | 异步状态管理 | API 调用、加载状态 |
| `useDebounce` | 防抖处理 | 搜索输入、窗口调整 |
| `useLocalStorage` | 本地存储响应式封装 | 持久化数据 |
| `usePagination` | 分页逻辑 | 列表分页 |
| `usePermission` | 权限检查 | 按钮级权限控制 |
| `useTheme` | 主题切换 | 深色/浅色模式 |

命名规范：使用 `use` 前缀，文件名与函数名一致，返回对象包含状态和方法。

### Composable vs Store

| 场景 | 推荐 |
|------|------|
| 组件内局部状态 | Composable |
| 跨组件共享状态 | Pinia Store |
| 一次性的逻辑封装 | Composable |
| 需要持久化的全局状态 | Pinia Store |

## 树结构支持

前端提供统一的树类型定义和工具函数：

- `framework/types/tree.ts`：TreeNode、TreeNodeTree、TreeComponentNode、TreeAction 接口
- `framework/utils/tree.ts`：buildTree、flattenTree、findNodeById、getAncestors、sortByTreeSorts 函数

## 测试

测试文件位于 `tests/` 目录，详见 [tests/CLAUDE.md](../tests/CLAUDE.md)。
