# Demo 开发指南

## 概述

Demo 模块是业务演示页面，作为路由的页面组件，提供健康检查、知识库管理等功能。

## 模块结构

```
demo/
├── api/           # API 客户端
├── assets/        # 静态资源
├── components/    # 业务组件
│   └── ui/        # UI 基基础组件
├── layouts/       # 布局组件
├── pages/         # 页面组件
├── router/        # 路由配置
├── stores/        # Pinia 状态管理
├── styles/        # 模块样式
└── types/         # TypeScript 类型定义
```

## 快速开始

### 健康检查 API

```typescript
import { apiClient } from '@/framework/api/client'

// 检查后端健康状态
const health = await apiClient.get('/health')
console.log(health.status) // 'healthy'
```

### 知识库管理

```typescript
import { useDatasetStore } from '@/demo/stores/datasets'

const store = useDatasetStore()

// 获取知识库列表
await store.fetchDatasets()

// 添加知识库
await store.addDataset({ name: '新知识库' })

// 删除知识库
await store.deleteDataset(id)
```

## 组件开发

### 页面组件

```vue
<template>
  <div class="page">
    <h1>{{ title }}</h1>
    <DatasetList :datasets="datasets" @delete="handleDelete" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDatasetStore } from '@/demo/stores/datasets'

const store = useDatasetStore()
const title = ref('知识库管理')

const datasets = computed(() => store.datasets)

onMounted(() => {
  store.fetchDatasets()
})

const handleDelete = async (id: string) => {
  await store.deleteDataset(id)
}
</script>
```

### 业务组件

```vue
<template>
  <div class="dataset-list">
    <div v-for="item in datasets" :key="item.id" class="dataset-item">
      <span>{{ item.name }}</span>
      <button @click="$emit('delete', item.id)">删除</button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Dataset {
  id: string
  name: string
}

interface Props {
  datasets: Dataset[]
}

defineProps<Props>()
defineEmits<{
  delete: [id: string]
}>()
</script>
```

## 状态管理

### Pinia Store

```typescript
import { defineStore } from 'pinia'
import { apiClient } from '@/framework/api/client'

interface Dataset {
  id: string
  name: string
  createdAt: string
}

export const useDatasetStore = defineStore('dataset', {
  state: () => ({
    datasets: [] as Dataset[],
    loading: false,
    error: null as Error | null
  }),

  actions: {
    async fetchDatasets() {
      this.loading = true
      try {
        this.datasets = await apiClient.get('/api/v1/datasets')
      } catch (e) {
        this.error = e as Error
      } finally {
        this.loading = false
      }
    },

    async addDataset(data: { name: string }) {
      const dataset = await apiClient.post('/api/v1/datasets', data)
      this.datasets.push(dataset)
    },

    async deleteDataset(id: string) {
      await apiClient.delete(`/api/v1/datasets/${id}`)
      this.datasets = this.datasets.filter(d => d.id !== id)
    }
  }
})
```

## API 端点

| 端点               | 方法   | 说明         |
|--------------------|--------|--------------|
| /health            | GET    | 健康检查     |
| /api/v1/datasets   | GET    | 获取知识库列表 |
| /api/v1/datasets   | POST   | 创建知识库   |
| /api/v1/datasets/:id | DELETE | 删除知识库 |

## 测试

所有测试位于 `tests/demo/` 目录：

```bash
# 运行所有测试
pnpm test:unit tests/demo/ --run

# 运行组件测试
pnpm test:unit tests/demo/components/ --run

# 运行 Store 测试
pnpm test:unit tests/demo/stores/ --run
```

## 注意事项

1. 页面组件通过路由懒加载
2. Store 使用 Pinia defineStore
3. API 调用统一使用 framework 的 apiClient
4. 类型定义放在 types/ 目录
