# Framework 模块开发指南

## 概述

Framework 模块是整体 UI 框架，提供统一的前端基础设施、模块系统、路由定义及各模块交互。

## 模块定位

Framework 是 Vue 前端的底层基础设施模块，提供路由、状态管理、布局、权限、API 客户端和模块系统等能力。

**依赖边界：** framework 禁止引用业务模块（如 `demo`、`iam`、`tenant`）。业务模块可以依赖 framework；framework 如需业务能力，必须通过 Protocol、注册器或启动期注入实现依赖倒置。

```text
demo / iam / tenant ──▶ framework
framework ──X──▶ demo / iam / tenant
```

## 模块结构

```
framework/
├── api/                       # API 客户端
│   └── client.ts              # Axios 封装
├── components/                # 框架级组件
│   └── ui/                    # UI 基础组件（模块组件）
│       ├── AppForm.vue        # 表单框架（保留）
│       └── AppFormItem.vue    # 表单项（保留）
├── directives/                # 自定义指令
│   └── permission.ts          # 权限指令
├── events/                    # 事件系统
│   └── index.ts               # EventBus、ModuleEvents
├── layouts/                   # 布局组件
│   ├── AdminLayout.vue        # 壳布局（使用 shadcn Sidebar）
│   └── components/            # 布局子组件
│       ├── AppNavMain.vue     # 分组侧边栏菜单
│       ├── AppNavbar.vue      # 顶部导航
│       ├── AppMain.vue        # 内容区
│       └── AppPage.vue        # 页面骨架
├── module/                    # 模块系统
│   ├── types.ts               # ModuleDescriptor、MenuItem 类型定义
│   ├── registry.ts            # ModuleRegistry 注册中心
│   ├── setup.ts               # setupFramework 初始化函数
│   └── index.ts               # 模块系统入口
├── pages/                     # 公共页面
│   ├── LoginPage.vue          # 登录页
│   ├── ForbiddenPage.vue      # 403 页
│   └── NotFoundPage.vue       # 404 页
├── router/                    # 路由配置
│   ├── index.ts               # 路由实例
│   └── guards.ts              # 路由守卫
├── stores/                    # 状态管理
│   ├── app.ts                 # 应用状态（device computed）
│   ├── user.ts                # 用户状态
│   ├── menu.ts                # 菜单状态
│   ├── permission.ts          # 权限状态
│   └── index.ts               # Store 聚合导出
├── styles/                    # 样式文件
│   ├── tokens.css             # 设计令牌
│   └── main.css               # 样式入口
├── types/                     # 类型定义
│   ├── index.ts               # 公共类型
│   └── tree.ts                # 树节点类型（TreeNode、TreeNodeTree、TreeComponentNode、TreeAction）
├── utils/                     # 工具函数
│   └── tree.ts                # 树工具函数（buildTree、flattenTree、findNodeById、getAncestors、sortByTreeSorts）
└── CLAUDE.md                  # 本文档
```

## 目录职责

| 目录 | 职责 |
|------|------|
| `api/` | Axios 封装、请求拦截、响应处理、错误处理 |
| `components/` | 框架级 UI 组件（AppForm、AppFormItem 等） |
| `directives/` | Vue 自定义指令（权限指令 v-permission） |
| `events/` | EventBus 事件总线、模块事件定义 |
| `layouts/` | 布局组件（AdminLayout、AppNavMain、AppPage 等） |
| `module/` | 模块动态加载系统：`ModuleDescriptor` 类型、`ModuleRegistry` 注册中心、`setupFramework` 初始化 |
| `pages/` | 公共页面（登录、403、404、设置页） |
| `router/` | 路由实例创建、静态路由配置、路由守卫 |
| `stores/` | Pinia Store（应用状态、用户状态、权限状态、菜单状态） |
| `styles/` | 设计令牌、CSS 变量、Tailwind 配置 |
| `types/` | TypeScript 类型定义（公共类型、树类型） |
| `utils/` | 工具函数（树工具、通用工具） |

## 开发规则

- 抽象能力优先定义在 `types/`，具体实现放在对应组件目录。
- 模块系统通过 `ModuleDescriptor` 协议定义，业务模块实现协议后注册到 `ModuleRegistry`。
- 路由守卫自动处理登录验证、权限检查，业务模块无需重复实现。
- API 客户端统一处理 token 注入、错误拦截、响应转换，业务模块通过 `apiClient` 调用。
- 跨模块状态通过 Pinia Store 共享，EventBus 用于模块间事件通信。

## 模块系统

Framework 提供前端模块系统，支持模块声明、注册、依赖验证和路由动态加载。

### 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `ModuleDescriptor` | `module/types.ts` | 模块描述符协议，定义模块的标准结构 |
| `ModuleRegistry` | `module/registry.ts` | 模块注册中心，管理模块注册、查询和路由收集 |
| `setupFramework` | `module/setup.ts` | 框架初始化函数，注册模块并配置路由 |
| `EventBus` | `events/index.ts` | 事件总线，用于模块间通信 |

### ModuleDescriptor 协议

每个业务模块必须实现 `ModuleDescriptor` 协议：

```typescript
interface ModuleDescriptor {
  name: string;                              // 模块名称，小写字母、数字、连字符
  version: string;                           // 模块版本，遵循 semver
  getRoutes: () => RouteRecordRaw[];         // 返回路由配置（必需）
  dependencies?: string[];                   // 依赖的其他模块名称
  icon?: string;                             // 模块图标标识
  getMenuItems?: () => MenuItem[];           // 返回菜单项
  getStores?: () => Record<string, unknown>; // 返回 Store 对象
  setup?: (app: App, pinia: Pinia) => void | Promise<void>; // 模块初始化函数
}
```

### 模块注册流程

```typescript
import { setupFramework, getModuleRegistry, getEventBus } from "@/framework/module";
import { demoModule } from "@/demo";
import { iamModule } from "@/iam";
import { tenantModule } from "@/tenant";

// 在应用入口初始化框架
await setupFramework({
  app,
  router,
  pinia,
  modules: [tenantModule, iamModule, demoModule],
});

// 获取模块注册中心
const registry = getModuleRegistry();
const module = registry.getModule("iam");
const allRoutes = registry.getRoutes();

// 获取事件总线
const eventBus = getEventBus();
eventBus.on(ModuleEvents.MODULE_LOADED, ({ name }) => {
  console.log(`Module loaded: ${name}`);
});
```

### 模块依赖验证

注册模块时，`ModuleRegistry` 自动验证依赖关系：

```typescript
// 假设 iam 模块依赖 tenant 模块
const iamModule: ModuleDescriptor = {
  name: "iam",
  dependencies: ["tenant"], // 依赖 tenant 模块
  // ...
};

// 如果 tenant 未注册，将抛出错误：
// Module 'iam' depends on 'tenant' which is not registered
```

### 路由动态注册

`setupFramework` 收集所有模块路由并动态注册到 Vue Router：

```typescript
// 模块路由将添加到 AdminLayout 父路由下
const moduleRoutes = registry.getRoutes();
for (const route of moduleRoutes) {
  router.addRoute(rootRoute.name, route);
}
```

## 设计令牌

### 颜色系统

| 语义 | 变量 | 色值 | 用途 |
|------|------|------|------|
| 页面背景 | `--color-surface` | `#F5F7FA` | 内容区、列表底 |
| 抬升面 | `--color-surface-raised` | `#FFFFFF` | 卡片、侧栏、顶栏 |
| 主色 | `--color-primary` | `#1677FF` | 主按钮、链接、菜单选中 |
| 辅色 | `--color-secondary` | `#FF5722` | 次要强调、徽章 |
| 成功 | `--color-success` | `#10B981` | 成功态 |
| 危险 | `--color-danger` | `#EF4444` | 错误、删除 |
| 文字 | `--color-text` | `#1F2937` | 正文 |
| 次要文字 | `--color-text-muted` | `#6B7280` | 说明、表头 |
| 边框 | `--color-border` | `#E5E7EB` | 卡片、输入框边框 |

### 使用方式

```css
/* CSS 中使用 */
.my-component {
  background-color: var(--color-primary);
  color: var(--color-text);
}

/* Tailwind 中使用 */
<div class="bg-primary text-text">...</div>
```

## 布局组件

### AdminLayout

```vue
<template>
  <AdminLayout />
</template>

<script setup>
import AdminLayout from "@/framework/layouts/AdminLayout.vue";
</script>
```

### 布局尺寸

| 组件 | 尺寸 |
|------|------|
| 侧边栏展开 | --sidebar-width（约 240px） |
| 侧边栏折叠 | --sidebar-width-icon（约 48-56px） |
| Header 高度 | 56px（3.5rem） |

### AppNavMain

分组侧边栏菜单组件，支持分组标题、子菜单展开/折叠、路由导航。

```typescript
interface AppNavGroup {
  title?: string;
  items: Array<AppNavItem | AppNavSub>;
}

interface AppNavItem {
  icon?: FunctionalComponent;
  title: string;
  url: string;
}

interface AppNavSub {
  icon?: FunctionalComponent;
  title: string;
  items: AppNavSubItem[];
}
```

Props:

- `items`: 菜单分组数据（可选，默认使用内置菜单）

### AppPage

页面骨架组件，统一所有业务页面的 title/eyebrow/description/actions 区域。

```vue
<AppPage
  title="用户管理"
  eyebrow="系统管理"
  description="管理系统中所有用户账号。"
  variant="list"
>
  <template #actions>
    <Button>新建用户</Button>
  </template>

  页面主体内容
</AppPage>
```

Props:

- `title`: 页面主标题（必填）
- `eyebrow`: 标题上方小字提示（可选）
- `description`: 页面功能描述（可选）
- `variant`: 页面变体（list/workbench/detail/governance，默认 list）

Slots:

- `actions`: 标题右侧操作按钮区
- `default`: 页面主体内容

页面变体说明：

| variant | 背景 | 适用场景 |
|---------|------|----------|
| list | bg-background | 列表页（默认） |
| workbench | bg-muted/20 | 工作台、沉浸式操作 |
| detail | bg-background | 详情页 |
| governance | bg-background | 系统管理页 |

## UI 组件

### AppButton

```vue
<AppButton variant="primary">主按钮</AppButton>
<AppButton variant="secondary">强调按钮</AppButton>
<AppButton variant="outline">描边按钮</AppButton>
<AppButton variant="ghost">幽灵按钮</AppButton>
<AppButton variant="danger">危险按钮</AppButton>
```

Props:

- `variant`: 按钮变体 (primary/secondary/outline/ghost/danger)
- `size`: 尺寸 (sm/md/lg)
- `disabled`: 禁用
- `loading`: 加载状态
- `block`: 块级按钮

### AppInput

```vue
<AppInput v-model="value" placeholder="请输入" />
<AppInput v-model="value" error="此项必填" />
```

Props:

- `modelValue`: 绑定值
- `type`: 输入类型
- `placeholder`: 占位符
- `disabled`: 禁用
- `error`: 错误信息
- `clearable`: 可清空

### AppCard

```vue
<AppCard title="标题">
  内容
</AppCard>

<AppCard>
  <template #header>自定义头部</template>
  内容
  <template #footer>自定义底部</template>
</AppCard>
```

### AppModal

```vue
<AppModal v-model="visible" title="标题">
  内容
</AppModal>
```

Props:

- `modelValue`: 显示状态
- `title`: 标题
- `size`: 尺寸 (sm/md/lg/xl)
- `closable`: 可关闭
- `maskClosable`: 点击遮罩关闭

### AppLoading

```vue
<AppLoading />
<AppLoading text="加载中..." />
<AppLoading fullscreen />
```

## 状态管理

### AppStore

```typescript
import { useAppStore } from "@/framework/stores";

const store = useAppStore();

// 获取设备类型（只读 computed，基于 window.innerWidth）
if (store.device === "mobile") {
  // 移动端逻辑
}
```

注：侧边栏状态由 shadcn Sidebar 组件内部管理，不再通过 AppStore 控制。

### UserStore

```typescript
import { useUserStore } from "@/framework/stores";

const store = useUserStore();

// 登录
store.setToken("token");
store.setUserInfo({ ... });

// 检查权限
store.hasPermission("user:add");
store.hasRole("admin");

// 登出
store.logout();
```

### PermissionStore

```typescript
import { usePermissionStore } from "@/framework/stores";

const store = usePermissionStore();

// 设置路由
store.setRoutes(routes);

// 检查权限
store.hasPermission(["user:add", "user:edit"]);
```

## 权限控制

### 路由守卫

自动处理：

- 未登录跳转登录页
- 已登录访问登录页跳转首页
- 白名单路由直接放行

### 权限指令

```vue
<!-- 单个权限 -->
<button v-permission="'user:add'">添加用户</button>

<!-- 多个权限（满足任一） -->
<button v-permission="['user:add', 'user:edit']">操作</button>
```

### API 拦截

API 客户端自动处理：

- 401: 清除 token，跳转登录页
- 403: 跳转 403 页面

## API 端点

- `/health` - 健康检查
- `/api/v1/datasets` - 知识库 CRUD

## 测试

测试文件位于 `tests/framework/` 目录：

```bash
# 运行所有测试
pnpm test:unit tests/framework/ --run

# 运行组件测试
pnpm test:unit tests/framework/components/ --run

# 运行 Store 测试
pnpm test:unit tests/framework/stores/ --run

# 运行模块系统测试
pnpm test:unit tests/framework/module/ --run
```

## 依赖倒置

当 framework 需要业务能力时，通过 Protocol 或注册器实现依赖倒置：

```typescript
// 定义抽象接口
interface AuthProvider {
  getToken(): string | null;
  getCurrentUser(): User | null;
  hasPermission(permission: string): boolean;
}

// framework 使用抽象接口
class ApiClient {
  constructor(private authProvider: AuthProvider) {}

  request(config: AxiosRequestConfig) {
    const token = this.authProvider.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return axios.request(config);
  }
}

// 业务模块实现接口
class IamAuthProvider implements AuthProvider {
  getToken() {
    return useUserStore().token;
  }

  getCurrentUser() {
    return useUserStore().userInfo;
  }

  hasPermission(permission: string) {
    return usePermissionStore().hasPermission(permission);
  }
}

// 应用启动时注入实现
const apiClient = new ApiClient(new IamAuthProvider());
```

## 注意事项

1. 设计令牌通过 CSS `@theme` 定义，Tailwind 自动识别
2. 所有 API 请求通过 `apiClient` 进行
3. 路由配置支持懒加载
4. 组件使用 Tailwind CSS 和 CSS 变量混合样式
5. 新增模块需要在应用入口注册到 `setupFramework`
6. 模块间通信使用 EventBus 或 Pinia Store，避免直接导入其他模块内部实现
