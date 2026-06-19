# Framework 组件 API 参考

本文档提供 Framework 模块各组件的详细 API 参考和使用示例。

## 设计令牌

### 颜色系统

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

壳布局组件，使用 shadcn Sidebar。

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

**Props:**

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 页面主标题 |
| eyebrow | string | 否 | 标题上方小字提示 |
| description | string | 否 | 页面功能描述 |
| variant | string | 否 | 页面变体（list/workbench/detail/governance） |

**Slots:**

| 插槽 | 说明 |
|------|------|
| actions | 标题右侧操作按钮区 |
| default | 页面主体内容 |

**页面变体说明:**

| variant | 背景 | 适用场景 |
|---------|------|----------|
| list | bg-background | 列表页（默认） |
| workbench | bg-muted/20 | 工作台、沉浸式操作 |
| detail | bg-background | 详情页 |
| governance | bg-background | 系统管理页 |

### AppNavMain

分组侧边栏菜单组件。

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

## UI 组件

### AppButton

```vue
<AppButton variant="primary">主按钮</AppButton>
<AppButton variant="secondary">强调按钮</AppButton>
<AppButton variant="outline">描边按钮</AppButton>
<AppButton variant="ghost">幽灵按钮</AppButton>
<AppButton variant="danger">危险按钮</AppButton>
```

**Props:**

| 属性 | 类型 | 说明 |
|------|------|------|
| variant | string | 按钮变体 (primary/secondary/outline/ghost/danger) |
| size | string | 尺寸 (sm/md/lg) |
| disabled | boolean | 禁用 |
| loading | boolean | 加载状态 |
| block | boolean | 块级按钮 |

### AppInput

```vue
<AppInput v-model="value" placeholder="请输入" />
<AppInput v-model="value" error="此项必填" />
```

**Props:**

| 属性 | 类型 | 说明 |
|------|------|------|
| modelValue | any | 绑定值 |
| type | string | 输入类型 |
| placeholder | string | 占位符 |
| disabled | boolean | 禁用 |
| error | string | 错误信息 |
| clearable | boolean | 可清空 |

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

**Props:**

| 属性 | 类型 | 说明 |
|------|------|------|
| modelValue | boolean | 显示状态 |
| title | string | 标题 |
| size | string | 尺寸 (sm/md/lg/xl) |
| closable | boolean | 可关闭 |
| maskClosable | boolean | 点击遮罩关闭 |

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

## 事件系统

### EventBus API

```typescript
import { getEventBus, ModuleEvents } from "@/framework/events";

const eventBus = getEventBus();

// 订阅事件，返回取消订阅函数
const unsubscribe = eventBus.on("event:name", (payload) => {
  console.log("Received:", payload);
});

// 发布事件
eventBus.emit("event:name", { data: "value" });

// 取消订阅
unsubscribe();
// 或
eventBus.off("event:name", handler);
```

### 预定义事件

| 事件常量 | 事件名 | 说明 | Payload 类型 |
|----------|--------|------|--------------|
| USER_LOGGED_IN | user:logged-in | 用户登录成功 | { id, name, email } |
| USER_LOGGED_OUT | user:logged-out | 用户登出 | null |
| TENANT_CHANGED | tenant:changed | 租户切换 | { id, name } |
| MODULE_LOADED | module:loaded | 模块加载完成 | { name } |
| MODULE_ERROR | module:error | 模块加载错误 | { name, error } |
| DATA_REFRESH_REQUESTED | data:refresh-requested | 数据刷新请求 | { source } |

### 使用示例

```vue
<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import { getEventBus, ModuleEvents } from "@/framework/events";

const eventBus = getEventBus();

// 定义事件处理器
function handleUserLogin(user) {
  console.log("User logged in:", user);
}

onMounted(() => {
  // 订阅事件
  const unsubscribes = [
    eventBus.on(ModuleEvents.USER_LOGGED_IN, handleUserLogin),
    eventBus.on(ModuleEvents.TENANT_CHANGED, (tenant) => {
      console.log("Tenant changed:", tenant);
    }),
  ];

  // 组件卸载时取消订阅
  onUnmounted(() => {
    unsubscribes.forEach((unsubscribe) => unsubscribe());
  });
});
</script>
```

### 自定义事件

```typescript
// 发布自定义事件
eventBus.emit("demo:custom-event", { message: "Hello" });

// 订阅自定义事件
eventBus.on("demo:custom-event", (payload) => {
  console.log(payload.message);
});
```

### 最佳实践

1. **事件命名**：使用 `{模块}:{动作}` 格式，如 `demo:data-updated`、`iam:role-changed`
2. **取消订阅**：在组件 `onUnmounted` 时取消订阅，避免内存泄漏
3. **类型安全**：为自定义事件定义 Payload 类型
4. **适度使用**：优先使用 Pinia Store 共享状态，EventBus 用于一次性事件通知

## 模块注册

### 注册流程

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

### 依赖验证

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

```typescript
// 模块路由将添加到 AdminLayout 父路由下
const moduleRoutes = registry.getRoutes();
for (const route of moduleRoutes) {
  router.addRoute(rootRoute.name, route);
}
```
