# Framework 开发指南

## 概述

Framework 模块是整体 UI 框架，提供统一的前端基础设施、路由定义及各模块交互。

## 模块结构

```
framework/
├── api/           # API 客户端（Axios 封装）
├── assets/        # 静态资源
├── components/    # 通用组件
│   └── ui/        # UI 基础组件
├── layouts/       # 布局组件
├── pages/         # 页面组件
├── router/        # 路由配置
├── stores/        # Pinia 状态管理
├── styles/        # 全局样式
└── types/         # TypeScript 类型定义
```

## 快速开始

### API 客户端

```typescript
import { apiClient } from '@/framework/api/client'

// GET 请求
const data = await apiClient.get('/health')

// POST 请求
const result = await apiClient.post('/api/v1/datasets', { name: 'test' })
```

### 路由配置

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('@/demo/pages/HomePage.vue') },
    { path: '/demo', component: () => import('@/demo/pages/DemoPage.vue') }
  ]
})
```

### 状态管理

```typescript
import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    loading: false,
    error: null as Error | null
  }),
  actions: {
    setLoading(value: boolean) {
      this.loading = value
    }
  }
})
```

### UI 组件

```vue
<template>
  <Button variant="primary" @click="handleClick">点击</Button>
  <Card title="标题">内容</Card>
  <Loading v-if="loading" />
</template>
```

## 设计模式

### Composable 函数

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

### API 拦截器

```typescript
// api/client.ts
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加认证 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error)
)
```

## 测试

所有测试位于 `tests/framework/` 目录：

```bash
# 运行所有测试
pnpm test:unit tests/framework/ --run

# 运行组件测试
pnpm test:unit tests/framework/components/ --run
```

## 注意事项

1. 所有 API 请求通过 `apiClient` 进行
2. 路由配置集中管理，支持懒加载
3. 使用 Pinia 进行状态管理
4. UI 组件使用 Tailwind CSS 样式
