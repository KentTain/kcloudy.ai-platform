# Demo 模块测试

本文件为 Claude Code 在 Demo 模块测试目录中工作时提供指导。

## 测试目录结构

```
tests/demo/
├── components/                # 组件测试
├── composables/               # Composable 测试
└── stores/                    # Store 测试
```

## 运行测试

### 运行所有测试

```bash
# 运行所有 demo 测试
pnpm test:unit tests/demo/ --run

# 运行组件测试
pnpm test:unit tests/demo/components/ --run

# 运行 Composable 测试
pnpm test:unit tests/demo/composables/ --run

# 运行 Store 测试
pnpm test:unit tests/demo/stores/ --run
```

## 测试规范

### 组件测试

使用 `@vue/test-utils` 的 `mount` 函数：

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DatasetList from '@/demo/components/DatasetList.vue'

describe('DatasetList', () => {
  it('renders dataset list', () => {
    const datasets = [
      { id: '1', name: 'Dataset 1' },
      { id: '2', name: 'Dataset 2' }
    ]
    
    const wrapper = mount(DatasetList, {
      props: { datasets }
    })
    
    expect(wrapper.findAll('.dataset-item')).toHaveLength(2)
  })

  it('emits delete event', async () => {
    const wrapper = mount(DatasetList, {
      props: { datasets: [{ id: '1', name: 'Test' }] }
    })
    
    await wrapper.find('.delete-btn').trigger('click')
    
    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')![0]).toEqual(['1'])
  })
})
```

### Composable 测试

```typescript
import { describe, expect, it } from 'vitest'
import { useDataset } from '@/demo/composables/useDataset'

describe('useDataset', () => {
  it('fetches datasets successfully', async () => {
    const { datasets, loading, fetchAll } = useDataset()
    
    await fetchAll()
    
    expect(loading.value).toBe(false)
    expect(datasets.value.length).toBeGreaterThan(0)
  })
})
```

### Store 测试

```typescript
import { describe, expect, it, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDatasetStore } from '@/demo/stores/datasets'

// Mock API
vi.mock('@/framework/api/client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve([
      { id: '1', name: 'Dataset 1' }
    ])),
    post: vi.fn(() => Promise.resolve({ id: '2', name: 'New' })),
    delete: vi.fn(() => Promise.resolve())
  }
}))

describe('DatasetStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('fetches datasets', async () => {
    const store = useDatasetStore()
    
    await store.fetchDatasets()
    
    expect(store.datasets).toHaveLength(1)
    expect(store.datasets[0].name).toBe('Dataset 1')
  })

  it('adds dataset', async () => {
    const store = useDatasetStore()
    
    await store.addDataset({ name: 'New Dataset' })
    
    expect(store.datasets).toHaveLength(1)
    expect(store.datasets[0].name).toBe('New')
  })

  it('deletes dataset', async () => {
    const store = useDatasetStore()
    store.datasets = [{ id: '1', name: 'Test' }]
    
    await store.deleteDataset('1')
    
    expect(store.datasets).toHaveLength(0)
  })
})
```

## 测试工具

### Mock API 响应

```typescript
import { vi } from 'vitest'

// Mock 成功响应
export function mockSuccessResponse(data: any) {
  return vi.fn(() => Promise.resolve(data))
}

// Mock 错误响应
export function mockErrorResponse(error: Error) {
  return vi.fn(() => Promise.reject(error))
}
```

### 测试夹具

```typescript
// fixtures/datasets.ts
export const mockDatasets = [
  { id: '1', name: 'Knowledge Base 1', createdAt: '2025-01-01' },
  { id: '2', name: 'Knowledge Base 2', createdAt: '2025-01-02' }
]

export const newDataset = {
  name: 'New Knowledge Base'
}
```

## 测试覆盖

| 模块       | 组件测试 | Composable 测试 | Store 测试 |
|------------|----------|-----------------|------------|
| api        | -        | -               | -          |
| components | ✅       | -               | -          |
| composables | -       | ✅              | -          |
| stores     | -        | -               | ✅         |
