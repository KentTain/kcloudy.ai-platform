# Demo 模块测试

本文件为 Claude Code 在 Demo 模块测试目录中工作时提供指导。

## 测试目录结构

```
tests/demo/
├── components/           # 组件测试
└── stores/               # Store 测试
```

## 运行测试

```bash
# 运行所有 Demo 测试
pnpm test:unit tests/demo/ --run

# 运行组件测试
pnpm test:unit tests/demo/components/ --run

# 运行 Store 测试
pnpm test:unit tests/demo/stores/ --run

# 生成覆盖率报告
pnpm test:unit tests/demo/ --run --coverage
```

## 测试分类

### 组件测试

| 目录 | 说明 |
|------|------|
| components/ | HomePage、HealthPage、DatasetsPage |

### Store 测试

| 目录 | 说明 |
|------|------|
| stores/ | DatasetsStore |

## 测试示例

### 页面组件测试

```typescript
import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import HealthPage from "@/demo/pages/HealthPage.vue";

// Mock API
vi.mock("@/demo/api/health", () => ({
  getHealth: vi.fn(() => Promise.resolve({ status: "healthy", timestamp: "2025-01-01" })),
}));

describe("HealthPage", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("renders correctly", () => {
    const wrapper = mount(HealthPage, {
      global: { plugins: [createPinia()] },
    });
    expect(wrapper.find(".health-page").exists()).toBe(true);
  });
});
```

### Store 测试

```typescript
import { describe, expect, it, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useDatasetStore } from "@/demo/stores/datasets";

// Mock API
vi.mock("@/demo/api/datasets", () => ({
  getDatasets: vi.fn(() => Promise.resolve([{ id: "1", name: "Test" }])),
}));

describe("DatasetsStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("fetches datasets", async () => {
    const store = useDatasetStore();
    await store.fetchDatasets();
    expect(store.datasets).toHaveLength(1);
  });
});
```

### API 测试

```typescript
import { describe, expect, it, vi } from "vitest";
import { getDatasets, createDataset } from "@/demo/api/datasets";

// Mock apiClient
vi.mock("@/framework/api/client", () => ({
  get: vi.fn(() => Promise.resolve({ data: [] })),
  post: vi.fn(() => Promise.resolve({ data: { id: "1" } })),
}));

describe("Datasets API", () => {
  it("gets datasets", async () => {
    const result = await getDatasets();
    expect(Array.isArray(result)).toBe(true);
  });

  it("creates dataset", async () => {
    const result = await createDataset({ name: "Test" });
    expect(result.id).toBe("1");
  });
});
```

## 测试覆盖

| 模块 | 组件测试 | Store 测试 | API 测试 |
|------|----------|------------|----------|
| pages | ✅ | - | - |
| stores | - | ✅ | - |
| api | - | - | ✅ |

## Mock 策略

### API Mock

```typescript
// Mock 整个 API 模块
vi.mock("@/demo/api/health", () => ({
  getHealth: vi.fn(),
}));

// 在测试中控制返回值
import { getHealth } from "@/demo/api/health";
(getHealth as any).mockResolvedValue({ status: "healthy" });
```

### Store Mock

```typescript
// Mock Pinia Store
vi.mock("@/demo/stores/datasets", () => ({
  useDatasetStore: vi.fn(() => ({
    datasets: [],
    loading: false,
    fetchDatasets: vi.fn(),
  })),
}));
```

## 最佳实践

1. Mock API 调用，避免真实网络请求
2. 测试加载状态和错误状态
3. 测试用户交互（点击、提交等）
4. 使用 beforeEach 初始化 Pinia
5. 清理 Mock 避免状态污染
