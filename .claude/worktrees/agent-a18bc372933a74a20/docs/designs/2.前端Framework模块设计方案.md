# 前端 Framework 模块设计方案

> **版本**：v1.0
> **更新日期**：2026-06-11
> **技术栈**：Vue 3.5 + TypeScript 5.8 + Vite 6.x

## 概述

Framework 是 Vue 前端的底层基础设施模块，为上层业务模块提供路由、状态管理、布局、权限控制、API 客户端和模块系统等核心能力。采用模块化设计，支持业务模块的动态加载和依赖管理。

## 架构设计

### 设计原则

1. **依赖倒置**：framework 通过接口定义抽象能力，业务模块实现具体逻辑，避免反向依赖
2. **模块化设计**：业务模块通过 `ModuleDescriptor` 声明式注册，框架自动加载、验证依赖、注册路由
3. **权限集中管理**：路由守卫、权限指令、API 拦截三层权限控制
4. **事件驱动**：EventBus 实现跨模块通信，支持松耦合的消息传递

### 模块分层

```text
┌─────────────────────────────────────────────────────────┐
│                     业务模块层                           │
│                   demo / iam / tenant                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Framework 基础设施层                   │
├─────────────────────────────────────────────────────────┤
│  pages/   │  layouts/  │  components/  │  composables/ │
├─────────────────────────────────────────────────────────┤
│   stores/   │   router/   │   api/   │   directives/   │
├─────────────────────────────────────────────────────────┤
│   module/   │   events/   │   utils/   │   styles/     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    类型定义层 (types/)                    │
│               TypeScript 接口 / 类型守卫                 │
└─────────────────────────────────────────────────────────┘
```

### 依赖边界

```
demo / iam / tenant ──▶ framework
framework ──X──▶ demo / iam / tenant
```

- 业务模块可以依赖 framework
- framework 禁止依赖业务模块
- 跨模块通信通过 EventBus 或 Pinia Store

## 子模块详细设计

### 1. module - 模块系统

**职责**：模块动态加载、注册中心、依赖验证、路由注册

#### 1.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `ModuleDescriptor` | `types.ts` | 模块描述符接口 |
| `ModuleRegistry` | `registry.ts` | 模块注册中心 |
| `setupFramework` | `setup.ts` | 框架初始化函数 |
| `isModuleDescriptor` | `types.ts` | 类型守卫函数 |

#### 1.2 ModuleDescriptor 接口

```typescript
interface ModuleDescriptor {
  /** 模块名称，小写字母、数字、连字符 */
  name: string;
  /** 模块版本，遵循 semver 格式 */
  version: string;
  /** 返回模块路由配置 */
  getRoutes: () => RouteRecordRaw[];
  /** 依赖的其他模块名称 */
  dependencies?: string[];
  /** 模块图标标识 */
  icon?: string;
  /** 返回菜单项数组 */
  getMenuItems?: () => MenuItem[];
  /** 返回 Store 对象 */
  getStores?: () => Record<string, unknown>;
  /** 模块初始化函数 */
  setup?: (app: App, pinia: Pinia) => void | Promise<void>;
}
```

#### 1.3 ModuleRegistry 设计

**核心功能**：
- 模块注册与去重
- 依赖验证（确保依赖模块已注册）
- 路由收集与合并
- 菜单项收集

**使用示例**：
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
```

#### 1.4 模块注册流程

```text
┌──────────────────────────────────────────────────────────┐
│                    setupFramework                        │
├──────────────────────────────────────────────────────────┤
│  1. 初始化全局 Registry 和 EventBus                      │
│  2. 遍历模块列表                                          │
│     ├── 验证模块描述符 (isModuleDescriptor)              │
│     ├── 验证依赖 (dependencies 已注册)                   │
│     ├── 注册到 Registry                                  │
│     ├── 调用模块 setup 函数                              │
│     └── 发出 MODULE_LOADED 事件                          │
│  3. 收集所有模块路由                                      │
│  4. 动态注册路由到 Vue Router                            │
└──────────────────────────────────────────────────────────┘
```

### 2. router - 路由系统

**职责**：路由实例创建、静态路由配置、路由守卫

#### 2.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `router` | `index.ts` | Vue Router 实例创建 |
| `setupRouterGuards` | `guards.ts` | 路由守卫配置 |

#### 2.2 路由守卫设计

**守卫流程**：
```text
┌──────────────────────────────────────────────────────────┐
│                    beforeEach 守卫                        │
├──────────────────────────────────────────────────────────┤
│  1. 设置页面标题                                         │
│  2. 白名单路由直接放行 (/login, /403, /404)             │
│  3. 预览页面直接放行 (/preview/*)                       │
│  4. 管理后台路由检查 (adminAuth)                         │
│     ├── 未登录 → 重定向 /admin/login                    │
│     └── 已登录 → 放行                                   │
│  5. 普通用户路由检查                                     │
│     ├── 未登录 → 重定向 /login                          │
│     ├── 已登录访问登录页 → 重定向首页                    │
│     ├── 权限检查 (meta.permissions)                     │
│     ├── 角色检查 (meta.roles)                           │
│     └── 加载菜单 (首次)                                 │
└──────────────────────────────────────────────────────────┘
```

**路由元信息**：
```typescript
interface RouteMeta {
  title?: string;           // 页面标题
  permissions?: string[];   // 所需权限码
  roles?: string[];         // 所需角色码
  requiresAdminAuth?: boolean; // 需要管理后台认证
}
```

### 3. stores - 状态管理

**职责**：应用状态、用户状态、权限状态、菜单状态、通知状态

#### 3.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `useAppStore` | `app.ts` | 应用状态（设备类型、侧边栏状态） |
| `useUserStore` | `user.ts` | 用户状态（用户信息、Token、租户） |
| `usePermissionStore` | `permission.ts` | 权限状态（菜单、权限检查） |
| `useMenuStore` | `menu.ts` | 菜单状态（菜单折叠、激活项） |
| `useNotificationStore` | `notification.ts` | 通知状态（消息列表、未读数） |

#### 3.2 UserStore 设计

```typescript
interface UserInfo {
  id: string;
  username: string;
  nickname: string;
  avatar?: string;
  email?: string;
  roles: string[];
  permissions: string[];
  tenantId?: string;
  tenantName?: string;
  tenantCode?: string;
  tenants?: TenantInfo[];
}

// 核心方法
const useUserStore = defineStore("user", () => {
  const userInfo = ref<UserInfo | null>(null);
  const token = ref<string | null>(localStorage.getItem("token"));
  const isLoggedIn = computed(() => !!token.value);
  const currentTenant = computed<TenantInfo | null>(() => {...});
  const tenants = computed<TenantInfo[]>(() => userInfo.value?.tenants || []);

  const setToken = (newToken: string) => {...};
  const setUserInfo = (info: UserInfo) => {...};
  const logout = () => {...};
  const hasPermission = (permission: string) => {...};
  const hasRole = (role: string) => {...};

  return { userInfo, token, isLoggedIn, currentTenant, tenants, ... };
});
```

#### 3.3 PermissionStore 设计

```typescript
interface MenuItem {
  id: string;
  name: string;
  path: string;
  icon?: string;
  children?: MenuItem[];
}

const usePermissionStore = defineStore("permission", () => {
  const menus = ref<MenuItem[]>([]);
  const isLoaded = ref(false);

  // 从后端获取用户菜单并过滤权限
  const fetchUserMenus = async (): Promise<void> => {...};

  // 检查权限
  const hasPermission = (permissions: string | string[]): boolean => {...};

  // 重置权限
  const resetPermission = () => {...};

  return { menus, isLoaded, fetchUserMenus, hasPermission, resetPermission };
});
```

### 4. api - API 客户端

**职责**：Axios 封装、请求拦截、响应处理、Token 管理

#### 4.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `apiClient` | `client.ts` | 默认 API 客户端（/api 前缀） |
| `rawApiClient` | `client.ts` | 无前缀 API 客户端 |
| `createApiClient` | `client.ts` | 工厂函数 |

#### 4.2 请求拦截器

```typescript
// 请求拦截器
instance.interceptors.request.use((config) => {
  // 根据请求路径判断使用哪个 token
  const isAdminRequest = config.url?.startsWith("/admin");
  const tokenKey = isAdminRequest ? "admin_token" : "token";
  const token = localStorage.getItem(tokenKey);

  if (token) {
    config.headers.Authorization = "Bearer " + token;
  }

  // 添加租户 ID 请求头
  const tenantId = localStorage.getItem("tenant_id");
  if (tenantId && !isAdminRequest) {
    config.headers["X-Tenant-Id"] = tenantId;
  }

  return config;
});
```

#### 4.3 响应拦截器

```typescript
// 响应拦截器
instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const { response, config } = error;
    const isAdminRequest = config?.url?.startsWith("/admin");

    // 401 未登录
    if (response?.status === 401) {
      if (isAdminRequest) {
        localStorage.removeItem("admin_token");
        window.location.href = "/admin/login";
      } else {
        localStorage.removeItem("token");
        window.location.href = "/login";
      }
    }

    // 403 无权限
    if (response?.status === 403) {
      window.location.href = "/403";
    }

    return Promise.reject(error);
  }
);
```

#### 4.4 快捷方法

```typescript
// 快捷请求方法
export const get = <T>(url: string, config?: AxiosRequestConfig): Promise<T>;
export const post = <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>;
export const put = <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>;
export const del = <T>(url: string, config?: AxiosRequestConfig): Promise<T>;

// 无前缀版本
export const rawGet = <T>(url: string, config?: AxiosRequestConfig): Promise<T>;
export const rawPost = <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>;
```

### 5. events - 事件系统

**职责**：跨模块通信、事件发布订阅

#### 5.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `EventBus` | `index.ts` | 事件总线类 |
| `ModuleEvents` | `index.ts` | 预定义事件常量 |
| `getEventBus` | `index.ts` | 获取全局实例 |

#### 5.2 EventBus 设计

```typescript
class EventBus {
  private handlers: Map<string, Set<EventHandler>> = new Map();

  // 订阅事件，返回取消订阅函数
  on(event: string, handler: EventHandler): () => void;

  // 发布事件
  emit(event: string, payload?: unknown): void;

  // 取消订阅
  off(event: string, handler: EventHandler): void;
}
```

#### 5.3 预定义事件

| 事件常量 | 事件名 | 说明 | Payload 类型 |
|----------|--------|------|--------------|
| `USER_LOGGED_IN` | user:logged-in | 用户登录成功 | `{ id, name, email }` |
| `USER_LOGGED_OUT` | user:logged-out | 用户登出 | `null` |
| `TENANT_CHANGED` | tenant:changed | 租户切换 | `{ id, name }` |
| `MODULE_LOADED` | module:loaded | 模块加载完成 | `{ name }` |
| `MODULE_ERROR` | module:error | 模块加载错误 | `{ name, error }` |
| `DATA_REFRESH_REQUESTED` | data:refresh-requested | 数据刷新请求 | `{ source }` |

#### 5.4 使用示例

```typescript
import { getEventBus, ModuleEvents } from "@/framework/events";

const eventBus = getEventBus();

// 订阅事件
const unsubscribe = eventBus.on(ModuleEvents.USER_LOGGED_IN, (user) => {
  console.log("User logged in:", user);
});

// 发布事件
eventBus.emit(ModuleEvents.TENANT_CHANGED, { id: "t001", name: "租户A" });

// 取消订阅
unsubscribe();
```

### 6. directives - 自定义指令

**职责**：权限指令、其他自定义指令

#### 6.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `permissionDirective` | `permission.ts` | 权限控制指令 |
| `setupPermissionDirective` | `permission.ts` | 注册权限指令 |

#### 6.2 v-permission 指令

```typescript
const permissionDirective: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding<string | string[]>) {
    const permissionStore = usePermissionStore();
    const permissions = Array.isArray(binding.value) ? binding.value : [binding.value];

    const hasPermission = permissionStore.hasPermission(permissions);

    if (!hasPermission) {
      el.parentNode?.removeChild(el);
    }
  },
};
```

**使用方式**：
```vue
<!-- 单个权限 -->
<button v-permission="'user:add'">添加用户</button>

<!-- 多个权限（满足任一） -->
<button v-permission="['user:add', 'user:edit']">操作</button>
```

### 7. layouts - 布局组件

**职责**：后台管理布局、侧边栏、顶部导航、内容区

#### 7.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `AdminLayout` | `AdminLayout.vue` | 后台管理壳布局 |
| `AppNavMain` | `components/AppNavMain.vue` | 侧边栏菜单导航 |
| `AppNavbar` | `components/AppNavbar.vue` | 顶部导航栏 |
| `AppMain` | `components/AppMain.vue` | 内容区容器 |
| `AppPage` | `components/AppPage.vue` | 页面骨架组件 |
| `AppTenantSwitcher` | `components/AppTenantSwitcher.vue` | 租户切换器 |
| `AppHeaderRight` | `components/AppHeaderRight.vue` | 顶部右侧功能区 |
| `AppContentHeader` | `components/AppContentHeader.vue` | 内容页导航栏 |

#### 7.2 AdminLayout 布局结构

```text
┌──────────────────────────────────────────────────────────┐
│                      AdminLayout                         │
├──────────────┬───────────────────────────────────────────┤
│              │  Header (顶部导航栏)                      │
│   Sidebar    │  ┌─────────────────────────────────────┐  │
│   (侧边栏)    │  │ AppContentHeader (内容页导航栏)     │  │
│              │  ├─────────────────────────────────────┤  │
│  ┌────────┐  │  │                                     │  │
│  │租户切换│  │  │         AppMain (内容区)            │  │
│  ├────────┤  │  │                                     │  │
│  │AppNav  │  │  │                                     │  │
│  │Main    │  │  │                                     │  │
│  │(菜单)  │  │  │                                     │  │
│  └────────┘  │  └─────────────────────────────────────┘  │
└──────────────┴───────────────────────────────────────────┘
```

#### 7.3 AppPage 页面骨架

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

**Props**：

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 页面主标题 |
| eyebrow | string | 否 | 标题上方小字提示 |
| description | string | 否 | 页面功能描述 |
| variant | string | 否 | 页面变体 |

**页面变体**：

| variant | 背景 | 适用场景 |
|---------|------|----------|
| list | bg-background | 列表页（默认） |
| workbench | bg-muted/20 | 工作台、沉浸式操作 |
| detail | bg-background | 详情页 |
| governance | bg-background | 系统管理页 |

### 8. composables - 组合式函数

**职责**：权限检查、菜单权限、命令面板、防抖搜索

#### 8.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `usePermission` | `usePermission.ts` | 权限检查组合函数 |
| `useMenuPermission` | `useMenuPermission.ts` | 菜单权限过滤 |
| `useCommandPalette` | `useCommandPalette.ts` | 命令面板状态 |
| `useDebouncedSearch` | `useDebouncedSearch.ts` | 防抖搜索 |
| `useColorMode` | `useColorMode.ts` | 主题模式切换 |

#### 8.2 usePermission 设计

```typescript
function usePermission() {
  const userStore = useUserStore();

  // 检查单个权限
  const hasPermission = (permission: string): boolean;

  // 检查任一权限
  const hasAnyPermission = (permissions: string[]): boolean;

  // 检查全部权限
  const hasAllPermissions = (permissions: string[]): boolean;

  // 检查角色
  const hasRole = (role: string): boolean;
  const hasAnyRole = (roles: string[]): boolean;
  const hasAllRoles = (roles: string[]): boolean;

  return {
    hasPermission, hasAnyPermission, hasAllPermissions,
    hasRole, hasAnyRole, hasAllRoles,
  };
}
```

### 9. styles - 样式系统

**职责**：设计令牌、CSS 变量、全局样式

#### 9.1 核心文件

| 文件 | 职责 |
|------|------|
| `tokens.css` | 设计令牌定义（@theme） |
| `main.css` | 全局样式入口 |

#### 9.2 设计令牌

```css
@theme {
  /* ========== 颜色令牌 ========== */

  /* 背景色 */
  --color-surface: #f5f7fa;
  --color-surface-raised: #ffffff;

  /* 主色 - 蔚蓝 */
  --color-primary: #1677ff;
  --color-primary-hover: #0958d9;
  --color-primary-active: #003eb3;
  --color-primary-subtle: #e8f3ff;

  /* 辅色 - 橙红 */
  --color-secondary: #ff5722;
  --color-secondary-hover: #e64a19;
  --color-secondary-subtle: #fff3e0;

  /* 语义色 */
  --color-success: #10b981;
  --color-danger: #ef4444;
  --color-warning: #f59e0b;

  /* 文本色 */
  --color-text: #1f2937;
  --color-text-muted: #6b7280;
  --color-text-disabled: #9ca3af;

  /* 边框色 */
  --color-border: #e5e7eb;
  --color-border-primary: rgba(22, 119, 255, 0.35);

  /* ========== 字体令牌 ========== */
  --font-sans: "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  --font-mono: ui-monospace, "Cascadia Code", monospace;

  /* ========== 圆角令牌 ========== */
  --radius-ui: 6px;
  --radius-sm: 4px;
  --radius-lg: 8px;

  /* ========== 阴影令牌 ========== */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);

  /* ========== 过渡动画 ========== */
  --transition-fast: 150ms ease;
  --transition-normal: 200ms ease;
  --transition-slow: 300ms ease;
}
```

#### 9.3 颜色系统

| 语义 | 变量 | 色值 | 用途 |
|------|------|------|------|
| 页面背景 | --color-surface | #F5F7FA | 内容区、列表底 |
| 抬升面 | --color-surface-raised | #FFFFFF | 卡片、侧栏、顶栏 |
| 主色 | --color-primary | #1677FF | 主按钮、链接、菜单选中 |
| 辅色 | --color-secondary | #FF5722 | 次要强调、徽章 |
| 成功 | --color-success | #10B981 | 成功态 |
| 危险 | --color-danger | #EF4444 | 错误、删除 |
| 文字 | --color-text | #1F2937 | 正文 |
| 次要文字 | --color-text-muted | #6B7280 | 说明、表头 |
| 边框 | --color-border | #E5E7EB | 卡片、输入框边框 |

### 10. pages - 公共页面

**职责**：登录页、403 页、404 页、设置页

#### 10.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `LoginPage` | `LoginPage.vue` | 用户登录页 |
| `ForbiddenPage` | `ForbiddenPage.vue` | 403 无权限页 |
| `NotFoundPage` | `NotFoundPage.vue` | 404 未找到页 |
| `AccountSettingsPage` | `AccountSettingsPage.vue` | 账号设置页 |
| `DeveloperSettingsPage` | `DeveloperSettingsPage.vue` | 开发者设置页 |
| `PreviewLayoutPage` | `PreviewLayoutPage.vue` | 布局预览页 |

### 11. components - 框架组件

**职责**：命令面板、表单组件

#### 11.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `CommandPalette` | `CommandPalette.vue` | 全局命令面板 |
| `AppForm` | `ui/AppForm.vue` | 表单容器组件 |
| `AppFormItem` | `ui/AppFormItem.vue` | 表单项组件 |

### 12. types - 类型定义

**职责**：TypeScript 类型定义、公共类型

#### 12.1 核心类型

```typescript
// 菜单项
interface MenuItem {
  id: string;
  name: string;
  path: string;
  icon?: string;
  children?: MenuItem[];
}

// 租户信息
interface TenantInfo {
  id: string;
  name: string;
  code: string;
}

// 用户信息
interface UserInfo {
  id: string;
  username: string;
  nickname: string;
  avatar?: string;
  email?: string;
  roles: string[];
  permissions: string[];
  tenantId?: string;
  tenantName?: string;
  tenantCode?: string;
  tenants?: TenantInfo[];
}
```

## 权限控制体系

### 三层权限控制

```text
┌──────────────────────────────────────────────────────────┐
│                    权限控制体系                           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  1. 路由守卫 (guards.ts)                           │  │
│  │     - 登录检查                                     │  │
│  │     - 权限码检查 (meta.permissions)               │  │
│  │     - 角色检查 (meta.roles)                       │  │
│  └────────────────────────────────────────────────────┘  │
│                           │                              │
│                           ▼                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │  2. 权限指令 (v-permission)                        │  │
│  │     - 按钮级权限控制                               │  │
│  │     - 无权限自动移除 DOM                           │  │
│  └────────────────────────────────────────────────────┘  │
│                           │                              │
│                           ▼                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │  3. API 拦截 (client.ts)                           │  │
│  │     - 401 自动跳转登录页                           │  │
│  │     - 403 自动跳转无权限页                         │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 权限检查流程

```typescript
// 1. 路由守卫检查
const requiredPermissions = to.meta?.permissions;
if (requiredPermissions) {
  const hasPermission = requiredPermissions.some(p => userStore.hasPermission(p));
  if (!hasPermission) {
    next("/403");
    return;
  }
}

// 2. 指令级检查
<button v-permission="'user:add'">添加用户</button>

// 3. Composable 检查
const { hasPermission } = usePermission();
if (hasPermission("user:add")) {
  // 有权限逻辑
}
```

## 模块开发规范

### 模块结构

每个业务模块必须包含：

```text
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

### 模块入口示例

```typescript
// src/demo/index.ts
import type { ModuleDescriptor } from "@/framework/module";
import { routes } from "./router";

export const demoModule: ModuleDescriptor = {
  name: "demo",
  version: "1.0.0",
  icon: "layers",
  dependencies: ["iam"], // 依赖 iam 模块

  getRoutes: () => routes,

  getMenuItems: () => [
    {
      title: "演示模块",
      path: "/demo",
      icon: "layers",
      children: [
        { title: "数据集", path: "/demo/datasets" },
        { title: "对话", path: "/demo/chat" },
      ],
    },
  ],

  setup: (app, pinia) => {
    console.log("Demo module initialized");
  },
};
```

### 路由配置示例

```typescript
// src/demo/router/index.ts
import type { RouteRecordRaw } from "vue-router";

export const routes: RouteRecordRaw[] = [
  {
    path: "/demo",
    name: "Demo",
    component: () => import("../pages/DemoLayout.vue"),
    meta: { title: "演示模块" },
    children: [
      {
        path: "datasets",
        name: "DemoDatasets",
        component: () => import("../pages/DatasetsPage.vue"),
        meta: {
          title: "数据集管理",
          permissions: ["dataset:view"],
        },
      },
    ],
  },
];
```

## 最佳实践

### 1. 跨模块通信

优先使用 EventBus 处理一次性事件通知：

```typescript
// 发布事件
eventBus.emit(ModuleEvents.DATA_REFRESH_REQUESTED, { source: "dataset-list" });

// 订阅事件
const unsubscribe = eventBus.on(ModuleEvents.DATA_REFRESH_REQUESTED, ({ source }) => {
  if (source !== "dataset-list") {
    refreshData();
  }
});

// 组件卸载时取消订阅
onUnmounted(unsubscribe);
```

### 2. 权限控制

多层权限保护：

```vue
<script setup>
import { usePermission } from "@/framework/composables";

const { hasPermission } = usePermission();
</script>

<template>
  <!-- 路由级：meta.permissions -->
  <!-- 指令级：v-permission -->
  <Button v-permission="'user:add'" @click="handleAdd">添加用户</Button>

  <!-- 逻辑级：hasPermission -->
  <div v-if="hasPermission('user:delete')">
    <Button variant="danger">删除用户</Button>
  </div>
</template>
```

### 3. 页面开发

使用 AppPage 统一页面结构：

```vue
<template>
  <AppPage
    title="数据集管理"
    eyebrow="AI 平台"
    description="管理训练数据集和测试数据集"
    variant="list"
  >
    <template #actions>
      <Button v-permission="'dataset:create'">新建数据集</Button>
    </template>

    <!-- 页面主体内容 -->
    <DataTable :data="datasets" :columns="columns" />
  </AppPage>
</template>
```

### 4. API 调用

使用统一的 API 客户端：

```typescript
import { get, post } from "@/framework/api/client";

// GET 请求
const datasets = await get<Dataset[]>("/v1/datasets");

// POST 请求
const result = await post<Dataset>("/v1/datasets", {
  name: "新数据集",
  type: "training",
});
```

## 总结

前端 Framework 模块是 Vue 应用的基石，通过以下设计确保系统的可维护性和可扩展性：

1. **模块化设计**：清晰的职责划分，低耦合高内聚
2. **依赖倒置**：业务模块实现 ModuleDescriptor，framework 调用抽象接口
3. **多层权限控制**：路由守卫、权限指令、API 拦截三层保护
4. **事件驱动**：EventBus 实现跨模块松耦合通信
5. **设计令牌**：统一的颜色、字体、间距系统，确保视觉一致性

---

## 相关文档

- [前端PC端设计规范及框架设计探索](./前端PC端设计规范及框架设计探索.md)
- [前端Vue的模块分离设计方案](./前端Vue的模块分离设计方案.md)
- [Framework 开发指南](../../web/vue/src/framework/CLAUDE.md)
- [Framework API 参考](../../web/vue/src/framework/API.md)
