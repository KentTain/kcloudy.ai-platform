# CLAUDE.md

本文件为 Claude Code 在 Vue 前端源码目录中工作时提供指导。

## 目录结构

```text
src/
├── components/                # 通用组件
├── composables/               # 组合式函数 (Vue)
├── demo/                      # Demo 业务模块（路由页面）
└── framework/                 # Framework UI框架模块（整体框架、路由）
```

## Framework 模块

Framework 模块是整体 UI 框架，提供统一的前端基础设施、路由定义及各模块交互。

### Framework 目录结构

```text
framework/
├── api/                       # API 客户端（Axios 封装）
├── assets/                    # 静态资源
├── components/                # 通用组件
│   └── ui/                    # UI 基础组件（Button, Card, Loading）
├── layouts/                   # 布局组件（MainLayout）
├── pages/                     # 页面组件
├── router/                    # 路由配置
├── stores/                    # Pinia 状态管理
├── styles/                    # 全局样式
└── types/                     # TypeScript 类型定义
```

### Framework 核心功能

| 组件       | 用途                                     |
|------------|------------------------------------------|
| api        | Axios 实例配置，请求/响应拦截器          |
| components | UI 基础组件（Button, Card, Loading）     |
| layouts    | 布局组件（MainLayout）                   |
| router     | 路由配置，路由守卫                       |
| stores     | 全局状态管理                             |

### Framework 设计模式

**Composable 函数：**

```typescript
// composables/useAsync.ts
export function useAsync<T>(asyncFn: () => Promise<T>) {
  const loading = ref(false)
  const error = ref<Error | null>(null)
  const data = ref<T | null>(null)

  const execute = async () => {
    loading.value = true
    error.value = null
    try {
      data.value = await asyncFn()
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  return { loading, error, data, execute }
}
```

**API 封装：**

```typescript
// api/client.ts
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error)
)
```

### Framework 快速使用

**API 调用：**

```typescript
import { apiClient } from '@/framework/api/client'

const data = await apiClient.get('/health')
```

**路由配置：**

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('@/demo/pages/HomePage.vue') }
  ]
})
```

## Demo 模块

Demo 模块是业务演示页面，作为路由的页面组件，提供健康检查、知识库管理等功能。

### Demo 目录结构

```text
demo/
├── api/                       # API 客户端
├── assets/                    # 静态资源
├── components/                # 业务组件
│   └── ui/                    # UI 基础组件
├── layouts/                   # 布局组件
├── pages/                     # 页面组件
├── router/                    # 路由配置
├── stores/                    # Pinia 状态管理
├── styles/                    # 模块样式
└── types/                     # TypeScript 类型定义
```

### Demo 组件规范

| 层级       | 职责                         |
|------------|------------------------------|
| Pages      | 页面组件，路由对应的视图     |
| Components | 可复用的 UI 组件             |
| Stores     | 模块状态管理                 |
| API        | HTTP 请求封装                |

### Demo API 层规范

- **职责**：HTTP 请求封装，类型定义
- **请求库**：Axios
- **响应处理**：统一错误处理，类型转换

### Demo Store 层规范

- **职责**：状态管理，数据缓存
- **组织形式**：使用 Pinia defineStore
- **命名**：useXxxStore

### Demo 组件开发规范

- **语法**：`<script setup lang="ts">`
- **Props**：使用 `defineProps` + `withDefaults`
- **Emits**：使用 `defineEmits`

### Demo 快速使用

**状态管理：**

```typescript
import { useDatasetStore } from '@/demo/stores/datasets'

const store = useDatasetStore()
await store.fetchDatasets()
```

## API 端点

- **`/health`** - 健康检查
- **`/api/v1/datasets`** - 知识库 CRUD

## 测试

测试文件位于 `tests/` 目录，详见 [tests/CLAUDE.md](../tests/CLAUDE.md)。
