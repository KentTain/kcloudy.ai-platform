# Demo 模块开发指南

## 概述

Demo 模块是业务演示页面，作为路由的页面组件，提供健康检查、知识库管理等功能。

## 模块结构

```
demo/
├── api/                       # API 客户端
│   ├── health.ts              # 健康检查 API
│   └── datasets.ts            # 知识库 API
├── components/                # 业务组件
├── pages/                     # 页面组件
│   ├── HomePage.vue           # 首页
│   ├── HealthPage.vue         # 健康检查页面
│   ├── DatasetsPage.vue       # 知识库列表页面
│   └── EventBusDemoPage.vue   # EventBus 示例页面
├── router/                    # 路由配置
│   └── index.ts               # Demo 模块路由
├── stores/                    # 状态管理
│   └── datasets.ts            # 知识库状态
├── types/                     # 类型定义
│   └── index.ts               # Demo 类型
└── CLAUDE.md                  # 本文档
```

## 页面组件

### HomePage 首页

展示平台介绍和功能特性。

```vue
<template>
  <HomePage />
</template>

<script setup>
import HomePage from "@/demo/pages/HomePage.vue";
</script>
```

### HealthPage 健康检查

调用后端 `/health` API 检查服务状态。

```vue
<template>
  <HealthPage />
</template>

<script setup>
import HealthPage from "@/demo/pages/HealthPage.vue";
</script>
```

功能：
- 显示后端健康状态
- 显示时间戳
- 支持刷新和重试

### DatasetsPage 知识库列表

展示知识库列表，支持 CRUD 操作。

```vue
<template>
  <DatasetsPage />
</template>

<script setup>
import DatasetsPage from "@/demo/pages/DatasetsPage.vue";
</script>
```

功能：
- 显示知识库列表
- 新建知识库
- 查看/删除知识库

### EventBusDemoPage EventBus 示例

演示事件总线的发布订阅模式，作为跨模块通信的参考示例。

```vue
<template>
  <EventBusDemoPage />
</template>

<script setup>
import EventBusDemoPage from "@/demo/pages/EventBusDemoPage.vue";
</script>
```

功能：
- 发布预定义事件（登录、登出、租户切换、数据刷新）
- 发布自定义事件
- 实时显示事件日志
- 展示事件订阅/取消订阅的正确用法

访问路径：`/demo/event-bus`

## API 封装

### 健康检查 API

```typescript
import { getHealth } from "@/demo/api/health";

// 获取健康状态
const status = await getHealth();
// { status: "healthy", timestamp: "2025-01-01T00:00:00Z" }
```

### 知识库 API

```typescript
import {
  getDatasets,
  getDataset,
  createDataset,
  updateDataset,
  deleteDataset
} from "@/demo/api/datasets";

// 获取列表
const datasets = await getDatasets();

// 获取详情
const dataset = await getDataset("id");

// 创建
const newDataset = await createDataset({ name: "知识库名称" });

// 更新
await updateDataset("id", { name: "新名称" });

// 删除
await deleteDataset("id");
```

## 状态管理

### DatasetsStore

```typescript
import { useDatasetStore } from "@/demo/stores/datasets";

const store = useDatasetStore();

// 获取列表
await store.fetchDatasets();

// 访问数据
const datasets = store.datasets;
const loading = store.loading;
const error = store.error;

// 添加知识库
await store.addDataset({ name: "新知识库" });

// 更新知识库
await store.editDataset("id", { name: "新名称" });

// 删除知识库
await store.removeDataset("id");
```

## 路由配置

Demo 模块路由在 `demo/router/index.ts` 中定义：

```typescript
export const demoRoutes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "Home",
    component: () => import("@/demo/pages/HomePage.vue"),
    meta: { title: "首页", icon: "home" },
  },
  {
    path: "/health",
    name: "Health",
    component: () => import("@/demo/pages/HealthPage.vue"),
    meta: { title: "健康检查", icon: "health" },
  },
  {
    path: "/datasets",
    name: "Datasets",
    component: () => import("@/demo/pages/DatasetsPage.vue"),
    meta: { title: "知识库", icon: "database" },
  },
  {
    path: "/demo/event-bus",
    name: "EventBusDemo",
    component: () => import("@/demo/pages/EventBusDemoPage.vue"),
    meta: { title: "EventBus 示例", icon: "bell" },
  },
];
```

路由元信息：
- `title`: 页面标题，用于面包屑和 TagsView
- `icon`: 菜单图标

## 类型定义

### HealthStatus

```typescript
interface HealthStatus {
  status: string;
  timestamp: string;
}
```

### Dataset

```typescript
interface Dataset {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}
```

### CreateDatasetParams

```typescript
interface CreateDatasetParams {
  name: string;
  description?: string;
}
```

## 开发规范

### 组件开发

- 使用 `<script setup lang="ts">` 语法
- Props 使用 `defineProps` + `withDefaults`
- Emits 使用 `defineEmits`
- 组合使用 Framework 提供的 UI 组件

### API 调用

- 使用 Framework 提供的 `apiClient`
- 在 `api/` 目录下定义 API 函数
- 返回类型明确标注

### 状态管理

- 使用 Pinia `defineStore`
- 在 `stores/` 目录下创建 Store
- 导出类型定义

## 测试

测试文件位于 `tests/demo/` 目录：

```bash
# 运行 Demo 模块测试
pnpm test:unit tests/demo/ --run

# 运行 Store 测试
pnpm test:unit tests/demo/stores/ --run
```

## 注意事项

1. Demo 模块使用 Framework 提供的布局和组件
2. API 调用通过 Framework 的 `apiClient` 进行
3. 新增页面需在 `router/index.ts` 添加路由配置
4. 新增 Store 需在 `stores/` 目录创建文件
5. EventBus 用于一次性事件通知，状态共享优先使用 Pinia Store

## EventBus 使用参考

EventBusDemoPage 页面展示了 EventBus 的正确使用方式：

```typescript
import { onMounted, onUnmounted } from "vue";
import { getEventBus, ModuleEvents } from "@/framework/events";

const eventBus = getEventBus();

onMounted(() => {
  // 订阅事件，保存取消订阅函数
  const unsubscribes = [
    eventBus.on(ModuleEvents.USER_LOGGED_IN, handleLogin),
    eventBus.on(ModuleEvents.TENANT_CHANGED, handleTenantChange),
  ];

  // 组件卸载时取消订阅
  onUnmounted(() => {
    unsubscribes.forEach((fn) => fn());
  });
});
```

关键点：
- 使用 `getEventBus()` 获取全局实例
- `on()` 返回取消订阅函数，务必在 `onUnmounted` 时调用
- 自定义事件命名使用 `{模块}:{动作}` 格式
