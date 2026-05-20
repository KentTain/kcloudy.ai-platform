# Framework 模块测试

本文件为 Claude Code 在 Framework 模块测试目录中工作时提供指导。

## 测试目录结构

```
tests/framework/
├── components/                # 组件测试
│   └── ui/                    # UI 组件测试
├── composables/               # Composable 测试
└── stores/                    # Store 测试
```

## 运行测试

### 运行所有测试

```bash
# 运行所有 framework 测试
pnpm test:unit tests/framework/ --run

# 运行组件测试
pnpm test:unit tests/framework/components/ --run

# 运行 Composable 测试
pnpm test:unit tests/framework/composables/ --run

# 运行 Store 测试
pnpm test:unit tests/framework/stores/ --run
```

## 测试规范

### 组件测试

使用 `@vue/test-utils` 的 `mount` 函数：

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from '@/framework/components/ui/Button.vue'

describe('Button', () => {
  it('renders correctly', () => {
    const wrapper = mount(Button, {
      props: { variant: 'primary' }
    })
    expect(wrapper.classes()).toContain('btn-primary')
  })

  it('emits click event', async () => {
    const wrapper = mount(Button)
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })
})
```

### Composable 测试

```typescript
import { describe, expect, it } from 'vitest'
import { useAsync } from '@/framework/composables/useAsync'

describe('useAsync', () => {
  it('handles successful async operation', async () => {
    const { loading, error, data, execute } = useAsync(() => 
      Promise.resolve('success')
    )
    
    await execute()
    
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
    expect(data.value).toBe('success')
  })

  it('handles error', async () => {
    const { error, execute } = useAsync(() => 
      Promise.reject(new Error('failed'))
    )
    
    await execute()
    
    expect(error.value).toBeInstanceOf(Error)
    expect(error.value?.message).toBe('failed')
  })
})
```

### Store 测试

```typescript
import { describe, expect, it, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from '@/framework/stores/app'

describe('AppStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with default state', () => {
    const store = useAppStore()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('sets loading state', () => {
    const store = useAppStore()
    store.setLoading(true)
    expect(store.loading).toBe(true)
  })
})
```

## 测试工具

### 常用工具函数

```typescript
// 测试辅助函数
export function createWrapper(component: any, options = {}) {
  return mount(component, {
    global: {
      plugins: [createPinia()],
      ...options.global
    },
    ...options
  })
}
```

### Mock API

```typescript
import { vi } from 'vitest'

// Mock apiClient
vi.mock('@/framework/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn()
  }
}))
```

## 测试覆盖

| 模块        | 组件测试 | Composable 测试 | Store 测试 |
|-------------|----------|-----------------|------------|
| api         | -        | -               | -          |
| components  | ✅       | -               | -          |
| composables | -        | ✅              | -          |
| stores      | -        | -               | ✅         |
